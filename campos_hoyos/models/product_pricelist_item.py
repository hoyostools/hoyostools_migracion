# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    product_tmpl_standard_price = fields.Float(
        string='Costo',
        related='product_tmpl_id.standard_price',
        precompute=True,
        store=True,
        readonly=True,
    )

    rentability = fields.Float(
        string='Rentabilidad',
        compute='_compute_rentability',
        precompute=True,
        store=True,
        readonly=True,
        index=True,
    )

    @api.depends('fixed_price', 'product_tmpl_standard_price')
    def _compute_rentability(self):
        for record in self:
            fixed_price = record.fixed_price or 0.0
            standard_price = record.product_tmpl_standard_price or 0.0
            record.rentability = ((fixed_price - standard_price) / fixed_price) if fixed_price else 0.0

    is_rentability_negative = fields.Boolean(
        string='Rentabilidad negativa',
        compute='_compute_is_rentability_negative',
        precompute=True,
        store=True,
        readonly=True,
        index=True,
    )

    @api.depends('rentability')
    def _compute_is_rentability_negative(self):
        for record in self:
            record.is_rentability_negative = bool(record.rentability < 0) if record.rentability else False
