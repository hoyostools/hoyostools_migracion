from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    bandera_s = fields.Boolean(
        string='Bandera',
        readonly=True,
    )