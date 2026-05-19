import math
from odoo import fields, models, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    margin_exception = fields.Boolean(string="Excepción Margen")
    aurorizar_recogen = fields.Boolean(string="Autorizar Recogen")
    error_excepciones = fields.Char(string="Error Excepciones")
    freight_authorized = fields.Boolean(string="Autoriza Flete")
    can_edit_d = fields.Boolean(compute='_compute_can_edit_')
    is_user_gerencial = fields.Boolean(compute="_compute_is_user_gerencial", store=False)
    total_packs_order = fields.Integer(string='Total Pacas del Pedido', compute='_compute_total_packs_order')
    show_group_total_packs = fields.Integer(string='Total Pacas del Pedido',compute='_compute_total_packs_order', store=True)
    packaging_order_observation = fields.Text(string='Totalidad del empaque de la orden')
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, domain="[('type', '=', 'contact')]")


    def _compute_is_user_gerencial(self):
        is_gerencial = self.env.user.has_group('campos_hoyos.group_gerencial')
        for record in self:
            record.is_user_gerencial = is_gerencial

    def _prepare_order_line_values(self, product_id, quantity, linked_line_id=False, no_variant_attribute_values=None,product_custom_attribute_values=None, **kwargs):
        res= super(SaleOrder, self)._prepare_order_line_values(product_id, quantity, linked_line_id=False, no_variant_attribute_values=None, product_custom_attribute_values=None, **kwargs)
        product = self.env['product.product'].browse(product_id)
        res['commission_per'] = product.product_tmpl_id.commission
        return res

    @api.depends('order_line.commission_per', 'order_line.price_unit', 'order_line.product_uom_qty',"order_line.agent_ids.amount")
    def _compute_commission_total(self):
        for order in self:
            for line in order.order_line:
                if line._origin.commission_per != line.commission_per and order.can_edit_d:
                    line._origin.sudo().commission_per = line.commission_per
                if line._origin.commission_per != line.commission_per and order.can_edit_d:
                    line._origin.sudo().price_subtotal = line.price_subtotal
                if not order.can_edit_d:
                    line.sudo().commission_per = line.sudo().product_id.product_tmpl_id.commission
            order.sudo().commission_total = sum(order.mapped("order_line.agent_ids.amount"))
        return

    @api.depends('order_line')
    def _compute_can_edit_(self):
        can_edit = self.env.user.has_group('purchase.group_purchase_user') or self.env.user.has_group('purchase.group_purchase_manager') or self.env.user.has_group('analista.compras') or self.env.user.has_group('sales_team.group_sale_manager') or self.env.user.has_group('dir.comerciales') or self.env.user.has_group('asistentes.comerciales')
        for user in self:
            user.can_edit_d = can_edit

    def action_sale_ok(self):
        if self.carrier_id.name == 'Despachos':
            for product in self.order_line:
                if product.product_template_id.not_send_dispatch:
                    raise UserError('El producto %s no se puede enviar por despacho' % product.product_id.name)
        return super(SaleOrder, self).action_sale_ok()

    @api.onchange('carrier_id')
    def compute_warehouse_id(self):
        for order in self:
            if order.carrier_id and order.carrier_id.warehouse_id:
                order.warehouse_id = order.carrier_id.warehouse_id
            else:
                default_warehouse_id = self.env['ir.default'].with_company(
                    order.company_id.id)._get_model_defaults('sale.order').get('warehouse_id')
                if order.state in ['draft', 'sent'] or not order.ids:
                    # Should expect empty
                    if default_warehouse_id is not None:
                        order.warehouse_id = default_warehouse_id
                    else:
                        order.warehouse_id = order.user_id.with_company(order.company_id.id)._get_default_warehouse_id()

    @api.onchange('partner_id')
    def carrier_id_default(self):
        for order in self:
            order.carrier_id = order.partner_id.property_delivery_carrier_id

    @api.depends('partner_id')
    def _compute_partner_shipping_id(self):
        for order in self:
            if order.partner_id:
                delivery = self.env['res.partner'].search([('parent_id', '=', order.partner_id.id), ('type', '=', 'delivery')])
                if delivery:
                    order.partner_shipping_id = delivery[0]
                else:
                    order.partner_shipping_id = order.partner_id
                invoice = self.env['res.partner'].search([('parent_id', '=', order.partner_id.id), ('type', '=', 'invoice')])
                if invoice:
                    order.partner_invoice_id = invoice[0]
                else:
                    order.partner_invoice_id = order.partner_id

    @api.depends('order_line.total_packs')
    def _compute_total_packs_order(self):
        for order in self:
            total_packs = 0
            for line in order.order_line:
                total_packs += line.total_packs
            order.total_packs_order = total_packs
            order.show_group_total_packs = total_packs

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    minimum_quantity_for_discount = fields.Float(string="Cantidad minima para descuento", related="product_template_id.valor_b")
    maximum_quantity_for_discount = fields.Float(string="Cantidad máxima para descuento", related="product_template_id.valor_a")
    range_discount = fields.Integer(string="Descuento rango", related="product_template_id.descuento_rango")
    discount_exceeds_range = fields.Integer("Descuento supera rango", related="product_template_id.descuento_mayor")
    fixed_price_ldp_publica = fields.Float(string="LdP Publica")
    fixed_price_retail = fields.Float(string="Detal")
    fixed_price_pos = fields.Float(string="Punto de Venta")
    commission_per = fields.Float(string='% Comisión')
    proyeccion_inventario = fields.Float(string='Proy. Inventario', related="product_id.proyeccion_inventario",store=True)
    precio_unitario_impuesto_excluido = fields.Float(string="Precio Unitario Impuesto Excluido", store=True,compute="_compute_precio_unitario_impuesto")
    precio_unitario_impuesto_incluido = fields.Float(string="Precio Unitario Impuesto Incluido", store=True,compute="_compute_precio_unitario_impuesto")
    cant_pack = fields.Integer(
        related='product_template_id.cant_pack',
        string='Cant. Paca'
    )
    total_packs = fields.Integer(string='Total pacas', compute='_compute_total_packs')
    product_brand_id = fields.Many2one(
        "product.brand", string="Marca", related="product_template_id.product_brand_id"
    )
    notas_logisticas = fields.Char(string="Notas logisticas",related="order_id.notas_logisticas")
    partner_shipping_id = fields.Many2one('res.partner',string="Dirección Entrega",related="order_id.partner_shipping_id")
    pricelist_id = fields.Many2one('product.pricelist',string="Lista de precios",related="order_id.pricelist_id")
    payment_term_id = fields.Many2one('account.payment.term',string="Términos de pago",related="order_id.payment_term_id")
    secuencia = fields.Integer(
        string='Número de linea',
        readonly=True,
        copy=False,
    )

    def create(self, vals_list):
        lines = super().create(vals_list)

        for line in lines:
            # Solo asigna si no tiene secuencia
            if not line.secuencia and line.order_id:
                max_secuencia = max(
                    line.order_id.order_line.mapped('secuencia') or [0]
                )

                line.secuencia = max_secuencia + 1

        return lines

    @api.onchange('product_template_id')
    @api.depends('product_template_id')
    def commission_percentage(self):
        for line in self:
            if line.product_template_id:
                line.commission_per = line.product_template_id.commission

    def write(self, values):
        record = super(SaleOrderLine, self).write(values)
        for line in self:
            if line.commission_per:
                line.agent_ids._compute_amount()
        return record

    @api.onchange('product_template_id')
    def compute_fixed_price_ldp_publica(self):
        for line in self:
            if line.product_template_id:
                pricelist = self.env["product.pricelist.item"].search([('product_tmpl_id', '=', line.product_template_id.id)])
                for item in pricelist:
                    if item.pricelist_id.display_name.lower() == 'ldp publica (cop)':
                        line.fixed_price_ldp_publica = item.fixed_price
                    elif item.pricelist_id.display_name.lower() == 'detal (cop)':
                        line.fixed_price_retail = item.fixed_price
                    elif item.pricelist_id.display_name.lower() == 'punto de venta (cop)':
                        line.fixed_price_pos = item.fixed_price

    @api.depends("product_uom_qty", "price_total", "price_subtotal")
    def _compute_precio_unitario_impuesto(self):
        for line in self:
            if line.product_uom_qty and line.price_total:
                line.precio_unitario_impuesto_incluido = line.price_total / line.product_uom_qty
            else:
                line.precio_unitario_impuesto_incluido = 0.0
            if line.product_uom_qty and line.price_subtotal:
                line.precio_unitario_impuesto_excluido = line.price_subtotal / line.product_uom_qty
            else:
                line.precio_unitario_impuesto_excluido = 0.0

    @api.onchange('product_uom_qty','cant_pack')
    @api.depends('product_uom_qty','cant_pack')
    def _compute_total_packs(self):
        for line in self:
            if line.cant_pack != 0 :
                line.total_packs = math.floor(line.product_uom_qty / line.cant_pack)
            else:
                line.total_packs = 0
