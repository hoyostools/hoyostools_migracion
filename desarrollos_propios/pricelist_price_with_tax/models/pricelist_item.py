from odoo import models, fields, api

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    price_with_tax = fields.Float(string='Precio con IVA')

    @api.onchange('fixed_price')
    def _onchange_fixed_price(self):
        for item in self:
            if item.fixed_price and item.product_tmpl_id.taxes_id:
                tax = item.product_tmpl_id.taxes_id[0]
                tax_percent = tax.amount or 0.0
                item.price_with_tax = item.fixed_price * (1 + (tax_percent / 100))

    @api.onchange('price_with_tax')
    def _onchange_price_with_tax(self):
        for item in self:
            if item.price_with_tax and item.product_tmpl_id.taxes_id:
                tax = item.product_tmpl_id.taxes_id[0]
                tax_percent = tax.amount or 0.0
                # Reversa: sacamos el precio base
                item.fixed_price = item.price_with_tax / (1 + (tax_percent / 100))
