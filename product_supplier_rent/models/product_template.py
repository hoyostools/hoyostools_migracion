from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    first_seller_estimated_cost = fields.Float(
        string='Costo Estimado',
        compute='_compute_first_seller_estimated_cost',
        store=True,
        readonly=True,
        digits=(16, 2),
    )
    first_seller_sale_suggested_price = fields.Float(
        string='Precio Venta Sugerido',
        compute='_compute_first_seller_sale_suggested_price',
        store=True,
        readonly=True,
        digits=(16, 2),
    )
    first_seller_sale_suggested_price_detal_rounded = fields.Float(
        string='Precio Sugerido Detal',
        compute='_compute_first_seller_detal_price_rounded',
        store=True,
        readonly=True,
        digits=(16, 0),
    )
    first_seller_sale_suggested_price_detal_rounded_without_tax = fields.Float(
        string='Precio Sugerido Detal Sin Impuestos',
        compute='_compute_first_seller_detal_rounded_without_tax',
        store=True,
        readonly=True,
        digits=(16, 3),
    )
    first_seller_sale_suggested_price_ptv_rounded = fields.Float(
        string='Precio Venta Sugerida PTV',
        compute='_compute_first_seller_sale_suggested_price_ptv_rounded',
        store=True,
        readonly=True,
        digits=(16, 0),
    )
    first_seller_sale_suggested_price_ptv_rounded_without_tax = fields.Float(
        string='Precio Venta Sugerida PTV Sin Impuestos',
        compute='_compute_first_seller_sale_suggested_price_ptv_rounded_without_tax',
        store=True,
        readonly=True,
        digits=(16, 3),
    )

    # -- FUNCIONES PTV --
    @api.depends('seller_ids.sale_suggested_price_ptv_rounded_without_tax')
    def _compute_first_seller_sale_suggested_price_ptv_rounded_without_tax(self):
        for rec in self:
            rec.first_seller_sale_suggested_price_ptv_rounded_without_tax = (
                rec.seller_ids[:1].sale_suggested_price_ptv_rounded_without_tax
                if rec.seller_ids else 0.0
            )

    @api.depends('seller_ids.sale_suggested_price_ptv_rounded')
    def _compute_first_seller_sale_suggested_price_ptv_rounded(self):
        for rec in self:
            rec.first_seller_sale_suggested_price_ptv_rounded = (
                rec.seller_ids[:1].sale_suggested_price_ptv_rounded
                if rec.seller_ids else 0.0
            )

    @api.depends('seller_ids.sale_suggested_price_detal_rounded_without_tax')
    def _compute_first_seller_detal_rounded_without_tax(self):
        for rec in self:
            rec.first_seller_sale_suggested_price_detal_rounded_without_tax = (
                rec.seller_ids[:1].sale_suggested_price_detal_rounded_without_tax
                if rec.seller_ids else 0.0
            )

    @api.depends('seller_ids.sale_suggested_price_detal_rounded')
    def _compute_first_seller_detal_price_rounded(self):
        for rec in self:
            rec.first_seller_sale_suggested_price_detal_rounded = (
                rec.seller_ids[:1].sale_suggested_price_detal_rounded if rec.seller_ids else 0.0
            )

    @api.depends('seller_ids.estimated_cost')
    def _compute_first_seller_estimated_cost(self):
        for rec in self:
            rec.first_seller_estimated_cost = rec.seller_ids[:1].estimated_cost if rec.seller_ids else 0.0

    @api.depends('seller_ids.sale_suggested_price')
    def _compute_first_seller_sale_suggested_price(self):
        for rec in self:
            rec.first_seller_sale_suggested_price = rec.seller_ids[:1].sale_suggested_price if rec.seller_ids else 0.