from odoo import models, fields, api

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_cashback = fields.Boolean(string='Es cashback', default=False)