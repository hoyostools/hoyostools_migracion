from odoo import fields, models, api, _

class StockRoute(models.Model):
    _inherit = 'stock.route'

    oleada_pos = fields.Boolean(string = "Oleadas en PTV")