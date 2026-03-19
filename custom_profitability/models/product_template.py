from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    renta_ganar = fields.Integer(
        string='Renta a Ganar',
        help='Porcentaje de renta a ganar para calcular el precio de lista.'
    )

    @api.onchange('renta_ganar', 'standard_price')
    def _compute_list_price(self):
        for product in self:
            if product.renta_ganar < 100:
                product.list_price = product.standard_price / ((100 - product.renta_ganar) / 100)
            else:
                product.list_price = 0

