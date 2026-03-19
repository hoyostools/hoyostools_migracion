import math
from odoo import models, fields, api


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'


    def write(self, vals):
        # Evitar recursión si viene desde supplierinfo
        if self.env.context.get('from_supplierinfo_sync'):
            return super().write(vals)
        res = super().write(vals)
        self._trigger_supplierinfo_recompute()
        return res

    def _trigger_supplierinfo_recompute(self):
        for item in self:
            if not item.product_tmpl_id:
                continue
            suppliers = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', item.product_tmpl_id.id)
            ])
            for supplier in suppliers:
                # Actualiza los precios correspondientes sin causar recursión
                if item.pricelist_id.name.lower().find('detal') != -1:
                    supplier.with_context(from_pricelist_sync=True).write({
                        'precio_actual': item.fixed_price
                    })
                elif item.pricelist_id.name.lower().find('punto de venta oficial') != -1:
                    supplier.with_context(from_pricelist_sync=True).write({
                        'precio_actual_ptv': item.fixed_price
                    })
                    
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        # Evitar recursión infinita
        if self.env.context.get('from_supplierinfo_sync'):
            return super().write(vals)

        res = super().write(vals)

        if 'list_price' in vals:
            for product in self:
                suppliers = self.env['product.supplierinfo'].search([
                    ('product_tmpl_id', '=', product.id)
                ])
                suppliers.with_context(from_product_sync=True).write({
                    'current_list_price': vals['list_price']
                })
        return res
                
class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'
    
    
    commission_factory = fields.Float(
        string='Comisión(%)',
        default=0.0,
        help='Porcentaje de comisión aplicado al precio de fábrica. '
    )

    rent_percentage = fields.Integer(
        string='Renta Mayor',
        default=0.0
    )
    sale_ok = fields.Boolean(
        string='Disponible para Venta',
        related='product_tmpl_id.sale_ok',
        store=True,
        readonly=True
    )

    purchase_ok = fields.Boolean(
        string='Disponible para Compra',
        related='product_tmpl_id.purchase_ok',
        store=True,
        readonly=True
    )

    promedio_consumo = fields.Integer(
        string='Promedio Consumo',
        related='product_tmpl_id.promedio_consumo',
        store=True,
        readonly=True
    )
    price_factory = fields.Float(string='Precio Fabrica', default=0.0, digits=(16, 4))
    currency_factory = fields.Selection(
        [('yuan', 'Yuan'), ('usd', 'USD')],
        string='Moneda Fabrica'
    )
    yuan_exchange = fields.Float(string='Cambio Yuan', default=1.0)
    liquidation_factor = fields.Float(string='Factor Liquidación', default=1.0)
    estimated_cost = fields.Float(
        string='Costo Estimado',
        compute='_compute_estimated_cost',
        store=True,
        readonly=True
    )
    costo_actual = fields.Float(
        string='Costo Actual',
        compute='_compute_costo_actual',
    )
    sale_suggested_price = fields.Float(
        string='P.Mayor Sugerido',
        compute='_compute_sale_suggested_price',
        store=True,
        digits=(16, 2),
        readonly=True,
        help='Precio de venta sugerido calculado a partir del Costo Estimado aplicando el % Renta.'
    )
    current_list_price = fields.Float(
        string="P.Mayor Actual",
    )
    purchase_manufacturer_pname = fields.Char(
        string='Nombre del Fabricante',
        compute='_compute_purchase_manufacturer_pname',
        readonly=True,
        store=True,
    )
    purchase_extreme_rentability = fields.Float(
        string='Rentabilidad Extrema',
        compute='_compute_purchase_extreme_rentability',
        store=True,
        readonly=True
    )
    purchase_ranking = fields.Float(
        string='Ranking de Compra',
        compute='_compute_purchase_ranking',
        store=True,
        readonly=True
    )
    purchase_proyeccion_inventario = fields.Float(
        string='Proyección de Inventario',
        compute='_compute_purchase_proyeccion_inventario',
        store=True,
        readonly=True
    )

    diferencia_precio_venta = fields.Float(
        string='Dif P.Mayor',
        compute='_compute_diferencia_precio_venta',
        store=True,
        readonly=True,
        help='Diferencia entre el Precio Venta Mayorista Actual y el Precio Venta Mayorista Sugerido'
    )
    rent_mayorista = fields.Float(
        string='Rent. Actual Mayorista (%)',
        compute='_compute_rents',
        store=True,
        readonly=True
    )
    def write(self, vals):
        # Evitar recursión si viene desde product o pricelist
        if self.env.context.get('from_product_sync') or self.env.context.get('from_pricelist_sync'):
            return super().write(vals)

        res = super().write(vals)

        for rec in self:
            # Actualizar lista de precios Detal
            if 'precio_actual' in vals:
                rec.with_context(from_supplierinfo_sync=True)._update_pricelist_price('Detal', vals['precio_actual'])

            # Actualizar lista de precios Punto de Venta Oficial
            if 'precio_actual_ptv' in vals:
                rec.with_context(from_supplierinfo_sync=True)._update_pricelist_price('Punto de Venta Oficial', vals['precio_actual_ptv'])

            # Actualizar precio del producto
            if 'current_list_price' in vals and rec.product_tmpl_id:
                rec.product_tmpl_id.with_context(from_supplierinfo_sync=True).write({
                    'list_price': vals['current_list_price']
                })
        return res

    def _update_pricelist_price(self, pricelist_name, price):
        pricelist = self.env['product.pricelist'].search([('name', 'ilike', pricelist_name)], limit=1)
        if not pricelist or not self.product_tmpl_id:
            return
        item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', self.product_tmpl_id.id)
        ], limit=1)
        if item:
            item.fixed_price = price
        else:
            self.env['product.pricelist.item'].create({
                'pricelist_id': pricelist.id,
                'product_tmpl_id': self.product_tmpl_id.id,
                'applied_on': '1_product',
                'compute_price': 'fixed',
                'fixed_price': price
            })
            
    @api.depends('current_list_price', 'precio_actual', 'precio_actual_ptv', 'costo_actual')
    def _compute_rents(self):
        for rec in self:
            costo = rec.costo_actual or 0.0

            # Rent. Mayorista
            clp = rec.current_list_price or 0.0
            rec.rent_mayorista = ((clp - costo) / clp * 100.0) if clp else 0.0

            # Rent. Detal
            pad = rec.precio_actual or 0.0
            rec.rent_detal = ((pad - costo) / pad * 100.0) if pad else 0.0

            # Rent. PTV
            pap = rec.precio_actual_ptv or 0.0
            rec.rent_ptv = ((pap - costo) / pap * 100.0) if pap else 0.0
            
    @api.depends('precio_actual_ptv')
    def _compute_diferencia_precio_ptv(self):
        for rec in self:
            rec.diferencia_precio_ptv = ((rec.sale_suggested_price_ptv_rounded_without_tax or 0.0) - (rec.precio_actual_ptv or 0.0)) / (rec.precio_actual_ptv or 1.0) * 100.0 if rec.precio_actual_ptv else 0.0

    @api.depends('precio_actual')
    def _compute_diferencia_precio_detal(self):
        for rec in self:
            rec.diferencia_precio_detal = ((rec.sale_suggested_price_detal_rounded_without_tax or 0.0) - (rec.precio_actual or 0.0)) / (rec.precio_actual or 1.0) * 100.0 if rec.precio_actual else 0.0
    
    @api.depends('current_list_price', 'sale_suggested_price')
    def _compute_diferencia_precio_venta(self):
        for rec in self:
            rec.diferencia_precio_venta = ((rec.sale_suggested_price or 0.0) - (rec.current_list_price or 0.0)) / (rec.current_list_price or 1.0) * 100.0 if rec.current_list_price else 0.0

    # @api.depends('product_tmpl_id.manufacturer_pname')
    def _compute_purchase_manufacturer_pname(self):
        for rec in self:
            rec.purchase_manufacturer_pname = rec.product_tmpl_id.manufacturer_pname if rec.product_tmpl_id else ''

    @api.depends('product_tmpl_id.extreme_rentability')
    def _compute_purchase_extreme_rentability(self):
        for rec in self:
            rec.purchase_extreme_rentability = rec.product_tmpl_id.extreme_rentability if rec.product_tmpl_id else 0.0
            
    @api.depends('product_tmpl_id.ranking')
    def _compute_purchase_ranking(self):
        for rec in self:
            rec.purchase_ranking = rec.product_tmpl_id.ranking if rec.product_tmpl_id else 0.0
            
    @api.depends('product_tmpl_id.proyeccion_inventario')
    def _compute_purchase_proyeccion_inventario(self):
        for rec in self:
            rec.purchase_proyeccion_inventario = rec.product_tmpl_id.proyeccion_inventario if rec.product_tmpl_id else 0.0
    
    @api.depends('product_tmpl_id')
    def _compute_precio_actual(self):
        pricelist = self.env['product.pricelist'].search([('name', 'ilike', 'Detal')], limit=1)
        for record in self:
            price = 0.0
            if pricelist and record.product_tmpl_id:
                pricelist_item = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', pricelist.id),
                    ('product_tmpl_id', '=', record.product_tmpl_id.id),
                ], limit=1)
                if pricelist_item:
                    price = pricelist_item.fixed_price
            record.precio_actual = price

    def _recompute_price_fields(self):
        self._compute_precio_actual()
        self._compute_diferencia_precio_detal()
        self._compute_precio_actual_ptv()
        self._compute_diferencia_precio_ptv()
            


    @api.depends('price', 'price_factory', 'commission_factory',
                'currency_factory', 'yuan_exchange', 'liquidation_factor', 'discount')
    def _compute_estimated_cost(self):
        for record in self:
            # Si no se indica "Moneda Fábrica", usamos el price estándar con descuento
            if not record.currency_factory:
                base = record.price or 0.0
                if record.discount:
                    base = base * (1 - record.discount / 100.0)
            else:
                # 1) Precio de fábrica + comisión: P / (1 - comisión)
                base = record.price_factory or 0.0
                if record.commission_factory:
                    denom_comm = 1 - (record.commission_factory / 100.0)
                    base = base / denom_comm if denom_comm > 0 else 0.0

                # 2) Conversión de moneda y factor de liquidación
                if record.currency_factory == 'yuan':
                    base = (base / (record.yuan_exchange or 1.0)) * (record.liquidation_factor or 1.0)
                elif record.currency_factory == 'usd':
                    base = base * (record.liquidation_factor or 1.0)
                else:
                    base = 0.0

            record.estimated_cost = base

            
    @api.depends('estimated_cost', 'product_id')
    def _compute_costo_actual(self):
        for rec in self:
            rec.costo_actual = rec.product_tmpl_id.standard_price if rec.product_tmpl_id else 0.0

    @api.depends('estimated_cost', 'rent_percentage')
    def _compute_sale_suggested_price(self):
        """Precio Venta Sugerida (redondeado a múltiplo de 10 hacia arriba)."""
        for rec in self:
            value = rec.estimated_cost or 0.0
            if rec.rent_percentage:
                denom = 1 - (rec.rent_percentage / 100.0)
                value = value / denom if denom > 0 else 0.0
            rec.sale_suggested_price = math.ceil(value / 10.0) * 10 if value > 0 else 0.0
            
    @api.depends('product_tmpl_id.list_price')
    def _compute_current_list_price(self):
        for rec in self:
            rec.current_list_price = rec.product_tmpl_id.list_price if rec.product_tmpl_id else 0.0
            
    def _get_first_sale_tax_percent(self):
        """Regresa el % efectivo del PRIMER impuesto de venta del producto (o plantilla, o por defecto de la compañía)."""
        self.ensure_one()
        Tax = self.env['account.tax']
        taxes = Tax
        if self.product_id and self.product_id.taxes_id:
            taxes = self.product_id.taxes_id
        elif self.product_tmpl_id and self.product_tmpl_id.taxes_id:
            taxes = self.product_tmpl_id.taxes_id
        elif self.company_id and self.company_id.account_sale_tax_id:
            taxes = self.company_id.account_sale_tax_id

        rate = 0.0
        if taxes:
            first = taxes[:1].with_company(self.company_id)
            # aplanar por si es grupo y sumar sólo porcentuales
            for t in first.flatten_taxes_hierarchy():
                if t.amount_type == 'percent':
                    rate += (t.amount or 0.0)
        return rate


    @staticmethod
    def _round_up_to_900(amount):
        if not amount or amount <= 0:
            return 0.0
        k = math.floor(amount / 1000.0)
        candidate = k * 1000 + 900
        return candidate if amount <= candidate else (k + 1) * 1000 + 900
            
    #______________________________________________________________
                        # === CÁLCULOS PTV ===
    #______________________________________________________________
    
    renta_ptv = fields.Integer(
        string='Renta PTV (%)',
        default=0
    )

    sale_suggested_price_ptv = fields.Float(
        string='Precio PTV Sugerido',
        compute='_compute_ptv_prices',
        store=True,
        digits=(16, 3),
        readonly=True
    )

    sale_suggested_price_ptv_without_tax = fields.Float(
        string='Precio PTV Sugerido Sin Impuesto',
        compute='_compute_suggested_ptv_price_without_tax',
        store=True,
        digits=(16, 3),
        readonly=True
    )

    sale_suggested_price_ptv_rounded = fields.Float(
        string='Precio Venta Sugerido PTV',
        compute='_compute_ptv_rounded',
        store=True,
        digits=(16, 0),
        readonly=True
    )

    sale_suggested_price_ptv_rounded_without_tax = fields.Float(
        string='P.PTV Sugerido',
        compute='_compute_suggested_ptv_rounded_without_tax',
        store=True,
        digits=(16, 3),
        readonly=True
    )
    precio_actual_ptv = fields.Float(
        string='P.PTV Actual',
        help='Busca el precio fijo del producto en la lista de precios llamada "Punto de Venta".'
    )
    rent_ptv = fields.Float(
        string='Rent. Actual PTV (%)',
        compute='_compute_rents',
        store=True,
        readonly=True
    )         
    diferencia_precio_ptv = fields.Float(
        string='Dif P.PTV',
        compute='_compute_diferencia_precio_ptv',
        store=True,
        readonly=True,
        help='Diferencia entre el Precio Actual PTV y el Precio Venta Sugerida PTV'
    )
    precio_actual_iva = fields.Float(
        string='P.Detal Actual + IVA',
        compute='_compute_precio_actual_con_iva',
        store=True,
        digits=(16, 3),
        readonly=True,
    )

    precio_actual_iva_ptv = fields.Float(
        string='P.PTV Actual + IVA',
        compute='_compute_precio_actual_con_iva',
        store=True,
        digits=(16, 3),
        readonly=True,
    )
    
    @api.depends('precio_actual', 'precio_actual_ptv',
                'product_id.taxes_id', 'product_tmpl_id.taxes_id',
                'company_id.account_sale_tax_id')
    def _compute_precio_actual_con_iva(self):
        for rec in self:
            rate = rec._get_first_sale_tax_percent()

            # Calcular precio_actual + IVA
            base_detal = rec.precio_actual or 0.0
            rec.precio_actual_iva = base_detal * (1.0 + rate / 100.0) if rate > 0 else base_detal

            # Calcular precio_actual_ptv + IVA
            base_ptv = rec.precio_actual_ptv or 0.0
            rec.precio_actual_iva_ptv = base_ptv * (1.0 + rate / 100.0) if rate > 0 else base_ptv
                
    @api.depends(
        'sale_suggested_price_ptv',
        'product_id.taxes_id', 'product_id.taxes_id.amount',
        'product_tmpl_id.taxes_id', 'product_tmpl_id.taxes_id.amount',
        'company_id.account_sale_tax_id', 'company_id.account_sale_tax_id.amount',
    )
    def _compute_suggested_ptv_price_without_tax(self):
        for rec in self:
            rate = rec._get_first_sale_tax_percent()
            inc = rec.sale_suggested_price_ptv or 0.0
            rec.sale_suggested_price_ptv_without_tax = (
                inc / (1.0 + rate / 100.0) if rate > 0 else inc
            )
             
    @api.depends('precio_actual', 'renta_ptv', 'product_id')
    def _compute_ptv_prices(self):
        for rec in self:
            base_price = rec.precio_actual or 0.0

            # Aplicar la renta_ptv como DESCUENTO
            if rec.renta_ptv:
                base_price *= (1 - rec.renta_ptv / 100.0)

            # Aplicar el IVA
            rate = rec._get_first_sale_tax_percent()
            precio_con_iva = base_price * (1.0 + rate / 100.0) if rate > 0 else base_price

            rec.sale_suggested_price_ptv = precio_con_iva

    @api.depends('sale_suggested_price_ptv')
    def _compute_ptv_rounded(self):
        for rec in self:
            rec.sale_suggested_price_ptv_rounded = self._round_up_to_900(rec.sale_suggested_price_ptv)
            
    @api.depends(
        'sale_suggested_price_ptv_rounded',
        'product_id.taxes_id', 'product_id.taxes_id.amount',
        'product_tmpl_id.taxes_id', 'product_tmpl_id.taxes_id.amount',
        'company_id.account_sale_tax_id', 'company_id.account_sale_tax_id.amount',
    )
    def _compute_suggested_ptv_rounded_without_tax(self):
        for rec in self:
            rate = rec._get_first_sale_tax_percent()  # % del primer impuesto
            inc = rec.sale_suggested_price_ptv_rounded or 0.0
            rec.sale_suggested_price_ptv_rounded_without_tax = (
                inc / (1.0 + rate/100.0) if rate > 0 else inc
            )
            
    #__________________________________________________________________
    #__________________________________________________________________
    
    
    #______________________________________________________________
                        # === CÁLCULOS DETAL ===
    #______________________________________________________________
    
    renta_detal = fields.Integer(
        string='Renta Detal (%)',
        default=0
    )
    sale_suggested_price_detal = fields.Float(
        string='Precio Detal Sugerido',
        compute='_compute_detal_price_included',
        store=True,
        digits=(16, 3),
        readonly=True,
        help='Precio de venta sugerida aplicando Renta Detal sobre el Precio Venta Sugerida base.'
    )
    sale_suggested_price_detal_without_tax = fields.Float(
        string='precio detal sin impuesto',
        compute='_compute_detal_price_without_tax',
        store=True,
        digits=(16, 3),  # sin redondeo, mostramos decimales
        readonly=True,
        help='Precio detal SIN impuestos correspondiente al precio de venta sugerida (Con impuesto, sin redondeado a …900).'
    )
    sale_suggested_price_detal_rounded = fields.Float(
        string='Precio Venta Sugerido Detal',
        compute='_compute_sale_suggested_price_detal_rounded',
        store=True,
        digits=(16, 0),   # termina en 900, sin decimales
        readonly=True,
        help='Precio detal CON impuesto redondeado hacia arriba al siguiente valor que termine en 900.'
    )
    sale_suggested_price_detal_rounded_without_tax = fields.Float(
        string='P.Detal Sugerido',
        compute='_compute_suggested_detal_rounded_without_tax',
        store=True,
        digits=(16, 3),
        readonly=True,
    )
    precio_actual = fields.Float(
        string='P.Detal Actual',
        help='Busca el precio fijo del producto en la lista de precios llamada "Detal".'
    )
    rent_detal = fields.Float(
        string='Rent. Actual Detal (%)',
        compute='_compute_rents',
        store=True,
        readonly=True
    )
    diferencia_precio_detal = fields.Float(
        string='Dif P.Detal',
        compute='_compute_diferencia_precio_detal',
        store=True,
        readonly=True,
        help='Diferencia entre el Precio Actual y el Precio Venta Sugerida Detal'
    )    
    
    @api.depends('product_tmpl_id')
    def _compute_precio_actual_ptv(self):
        pricelist = self.env['product.pricelist'].search([('name', 'ilike', 'Punto de Venta Oficial')], limit=1)
        for record in self:
            price = 0.0
            if pricelist and record.product_tmpl_id:
                pricelist_item = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', pricelist.id),
                    ('product_tmpl_id', '=', record.product_tmpl_id.id),
                ], limit=1)
                if pricelist_item:
                    price = pricelist_item.fixed_price
            record.precio_actual_ptv = price
            
    @api.depends(
        'sale_suggested_price', 'renta_detal',
        'product_id', 'product_id.taxes_id', 'product_id.taxes_id.amount',
        'product_tmpl_id', 'product_tmpl_id.taxes_id', 'product_tmpl_id.taxes_id.amount',
        'company_id', 'company_id.account_sale_tax_id', 'company_id.account_sale_tax_id.amount',
    )
    def _compute_detal_price_included(self):
        """Precio CON impuesto (sin redondear)."""
        for rec in self:
            # base SIN IVA: partir de sale_suggested_price y aplicar renta_detal como margen
            base_no_tax = rec.sale_suggested_price or 0.0
            if rec.renta_detal:
                denom = 1 - (rec.renta_detal / 100.0)
                base_no_tax = base_no_tax / denom if denom > 0 else 0.0

            rate = rec._get_first_sale_tax_percent()  # %
            price_inc = base_no_tax * (1.0 + rate / 100.0) if rate > 0 else base_no_tax
            rec.sale_suggested_price_detal = price_inc


    @api.depends(
        'sale_suggested_price_detal',
        'product_id', 'product_id.taxes_id', 'product_id.taxes_id.amount',
        'product_tmpl_id', 'product_tmpl_id.taxes_id', 'product_tmpl_id.taxes_id.amount',
        'company_id', 'company_id.account_sale_tax_id', 'company_id.account_sale_tax_id.amount',
    )
    def _compute_detal_price_without_tax(self):
        """Precio SIN impuesto derivado del incluido (sin redondear)."""
        for rec in self:
            rate = rec._get_first_sale_tax_percent()  # %
            inc = rec.sale_suggested_price_detal or 0.0
            rec.sale_suggested_price_detal_without_tax = (
                inc / (1.0 + rate / 100.0) if rate > 0 else inc
            )
            
            
    @api.depends('sale_suggested_price_detal')
    def _compute_sale_suggested_price_detal_rounded(self):
        for rec in self:
            val = rec.sale_suggested_price_detal or 0.0
            rec.sale_suggested_price_detal_rounded = self._round_up_to_900(val)
            
    
    @api.depends(
        'sale_suggested_price_detal_rounded',
        'product_id.taxes_id', 'product_id.taxes_id.amount',
        'product_tmpl_id.taxes_id', 'product_tmpl_id.taxes_id.amount',
        'company_id.account_sale_tax_id', 'company_id.account_sale_tax_id.amount',
    )
    def _compute_suggested_detal_rounded_without_tax(self):
        for rec in self:
            rate = rec._get_first_sale_tax_percent()  # % del primer impuesto
            inc = rec.sale_suggested_price_detal_rounded or 0.0
            rec.sale_suggested_price_detal_rounded_without_tax = (
                inc / (1.0 + rate/100.0) if rate > 0 else inc
            )
    #__________________________________________________________________
    #__________________________________________________________________