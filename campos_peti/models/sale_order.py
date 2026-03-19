from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_due = fields.Float()
    due_days = fields.Float()
    exceeded_amount = fields.Float()
    credit_limit = fields.Float()
    print_image = fields.Binary()
    packaging_order_observation = fields.Char()
    image_sizes = fields.Char()
    onhand_check = fields.Boolean()
    forecast_check = fields.Boolean()
    bandera_s = fields.Boolean()
    force_invoiced = fields.Boolean()