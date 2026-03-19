from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    image_small = fields.Boolean()
    visible_sequence = fields.Char()
    qty_available = fields.Float()
    forecast_quantity = fields.Float()