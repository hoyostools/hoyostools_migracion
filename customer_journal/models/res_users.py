from odoo import _, api, models, fields


class ResUser(models.Model):
    _inherit = "res.users"

    account_journal_id = fields.Many2many('account.journal', string="Diarios habilitados")