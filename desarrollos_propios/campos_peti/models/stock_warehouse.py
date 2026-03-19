from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    customer_journal_id = fields.Many2one(
        'account.journal')
    vendor_journal_id = fields.Many2one(
        'account.journal')