# Copyright 2021 VentorTech OU
# Part of Ventor modules. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    barcode_ids = fields.One2many(
        'product.barcode.multi',
        'product_id',
        string='Additional Barcodes',
    )

    # THIS IS OVERRIDE SQL CONSTRAINTS.
    _sql_constraints = [
        ('barcode_uniq', 'check(1=1)', 'No error')
    ]

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        res = super()._name_search(name, domain=domain, operator=operator, limit=limit, order=order)
        domain = domain or []
        if name and not res:
            product_ids = list(self._search([('barcode_ids.name', operator, name)] + domain, limit=limit, order=order))
            return product_ids
        return res

    @api.constrains('barcode', 'barcode_ids', 'active')
    def _check_unique_barcode(self):
        barcodes_duplicate = []
        for product in self:
            barcode_names = []
            if product.barcode_ids:
                barcode_names = product.mapped('barcode_ids.name')
            if product.barcode:
                barcode_names.append(product.barcode)
            if not barcode_names:
                continue
            products = self.env['product.product'].search([
                ('barcode', 'in', barcode_names),
                ('id', '!=', product.id),
                ('active', '=', True),
            ])
            barcode_ids = self.env['product.barcode.multi'].search([
                ('name', 'in', barcode_names),
                ('product_id', '!=', product.id),
                ('product_id.active', '=', True),
            ])
            if len(barcode_names) != len(set(barcode_names)):
                barcodes_multi = set([barcode for barcode in barcode_names if barcode_names.count(barcode) > 1])
                for barcode in barcodes_multi:
                    barcodes_duplicate.append(barcode)
            if barcode_ids:
                barcodes = [barcode.name for barcode in barcode_ids]
                for barcode in barcodes:
                    barcodes_duplicate.append(barcode)
            if products:
                barcodes_product = [product.barcode for product in products]
                for barcode in barcodes_product:
                    barcodes_duplicate.append(barcode)
        if barcodes_duplicate:
            raise UserError(
                _(
                    "The following barcode(s): {0} was found in other active products."
                    "\nNote that product barcodes should not repeat themselves both in "
                    '"Barcode" field and "Additional Barcodes" field.'
                ).format(", ".join(set(barcodes_duplicate)))
            )
