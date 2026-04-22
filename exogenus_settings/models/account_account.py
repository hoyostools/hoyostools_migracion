from odoo import api, fields, models

class AccountAccount(models.Model):

    _inherit = "account.account"

    is_bank_account = fields.Boolean(string="Bank")
    bank_id = fields.Many2one('res.bank', string="Associate Bank")
