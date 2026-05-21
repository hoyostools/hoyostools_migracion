from odoo import _, api, models
from urllib3 import fields


class ResUser(models.Model):
    _inherit = "res.users"

    account_journal_id = fields.Many2many('account.journal', string="Diarios habilitados")