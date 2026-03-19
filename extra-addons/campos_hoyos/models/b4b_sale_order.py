from odoo import models, fields, api


class B4BSaleOrder(models.Model):
    _inherit = 'b4b.sale.order'

    guia_url = fields.Char(
        string='Guía',
        widget='url')