# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    caja_externa_qty = fields.Float(
        string="Cant. Caja Externa",
        compute="_compute_packaging_qty",
        store=False,
        readonly=True,
        help="Cantidad incluida en la Caja Externa del producto"
    )


    caja_interna_qty = fields.Float(
        string="Cant. Caja Interna",
        compute="_compute_packaging_qty",
        store=False,
        readonly=True,
        help="Cantidad incluida en la Caja Interna del producto"
    )

    @api.depends('product_id')
    def _compute_packaging_qty(self):
        for line in self:

            line.caja_externa_qty = line.product_id.packaging_ids.filtered(
                lambda p: p.name == "Caja Externa" or p.name == "Externo" or p.name == "Master"
            ).qty or 0.0

            line.caja_interna_qty = line.product_id.packaging_ids.filtered(
                lambda p: p.name == "Caja Interna"
            ).qty or 0.0


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    not_send_dispatch = fields.Boolean(string='No enviar por despacho', default=False)
    commission = fields.Float(string='% Comisión', default=0.0, required=True)
    auction = fields.Boolean(string="En remate")
    warranty_offered_by_supplier = fields.Boolean(string="Garantía ofrecida por proveedor")
    ranking = fields.Integer(string="Ranking")
    promedio_consumo = fields.Integer(string="Prom. Consumo")
    cant_pack = fields.Integer(string="Cant. Paca")

    pricelist_additional_discount_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Lista de precios de descuento adicional',
        default=lambda self: self.env['product.pricelist'].search([('name', 'ilike', 'Descuento Adicional')], limit=1),
    )

    additional_discount = fields.Float(
        string='Descuento adicional',
        compute='_compute_additional_discount',
        precompute=True,
        store=True,
        readonly=True,
        index=True,
    )

    proyeccion_inventario = fields.Float(compute='_compute_proyeccion_inventario', string='Proy. Inventario', precompute=True,store=True,readonly=True,index=True) #Existencias

    inventory_projection = fields.Char(string='Proyección inventario') #Reordenamiento

    average_ptv = fields.Integer(string="Promedio consumo PTV", default=0)
    average_retail = fields.Integer(string="Promedio consumo Retail", default=0)
    stand_ptv = fields.Char(string="Stand Ptv", default="")

    @api.depends('product_variant_ids')
    def _compute_proyeccion_inventario(self):
        for p in self:
            p.sudo().proyeccion_inventario = p.product_variant_ids[:1].proyeccion_inventario if p.product_variant_ids else 0

    @api.depends('product_variant_ids')
    def _compute_product_variant_id(self):
        super(ProductTemplate, self)._compute_product_variant_id()
        self._compute_proyeccion_inventario()

    @api.depends('pricelist_additional_discount_id.item_ids.price_discount')
    def _compute_additional_discount(self):
        for record in self:
            item = record.pricelist_additional_discount_id.item_ids.filtered(
                lambda x: x.product_tmpl_id == record
            )[:1] if record.pricelist_additional_discount_id else False
            record.additional_discount = item.price_discount if item else 0.0

    extreme_rentability = fields.Float(
        string='Rentabilidad extrema',
        compute='_compute_extreme_rentability',
        # precompute=True,
        store=True,
        readonly=True,
        index=True,
    )

    # @api.depends('list_price', 'descuento_mayor', 'additional_discount', 'standard_price')
    def _compute_extreme_rentability(self):
        '''
        VARIABLES:

        B1 = Precio de venta (list_price)
        B2 = Descuento adicional
        B3 = Descuento fijo (14%)
        B4 = Descuento VIP (3%)
        B5 = Descuento por volumen (descuento_mayor)
        P1 = Precio neto
        C1 = Costo (standard_price)
        R1 = Rentabilidad extrema

        FÓRMULAS:
        P1 = (((B1 * (1 - B2%) * (1 - B3%)) * (1 - B4%)) * (1 - B5%))
        R1 = (P1 - C1) / P1
        '''
        for record in self:
            B1 = record.list_price or 0.0
            B2 = record.additional_discount or 0.0
            B3 = 14
            B4 = 3
            B5 = record.descuento_mayor or 0.0
            C1 = record.standard_price or 0.0
            P1 = (((B1 * (1 - (B2 / 100)) * (1 - (B3 / 100))) * (1 - (B4 / 100))) * (1 - (B5 / 100)))
            record.extreme_rentability = (((P1 - C1) / P1) * 100) if P1 else 0.0

    is_rentability_negative = fields.Boolean(
        string='Rentabilidad negativa',
        compute='_compute_is_rentability_negative',
        precompute=True,
        store=True,
        readonly=True,
        index=True,
    )

    @api.depends('extreme_rentability')
    def _compute_is_rentability_negative(self):
        for record in self:
            record.is_rentability_negative = bool(record.extreme_rentability < 0) if record.extreme_rentability else False

    def write(self, vals):
        if any(item in vals for item in ['list_price', 'descuento_mayor', 'additional_discount', 'standard_price']):
            self._compute_extreme_rentability()
        return super().write(vals)
