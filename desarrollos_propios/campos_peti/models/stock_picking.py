from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    invoice_count = fields.Integer()
    invoice_counter = fields.Integer()
    operation_code = fields.Integer()
    is_return = fields.Boolean()
    automatic_send_dian = fields.Boolean()
    validate_packaging_order_observation = fields.Char()
    packaging_order_observation = fields.Char()
    buy_to_resupply_verification = fields.Char()
    product_criteria_update_finished = fields.Char()