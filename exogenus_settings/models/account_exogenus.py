from odoo import fields, models

class AccountExogenus(models.Model):
    _name = 'account.exogenus'
    _description = 'Account Exogenus'

    #  campos conceptos
    name = fields.Char(string="Account Name", related="account_id.code", store=True)
    account_id = fields.Many2one('account.account', string="Account")
    format_exogenus_account_id = fields.Many2one('format.exogenus')
    is_account_daily = fields.Boolean(string="Saldos Exogena")
    exogena_journal_ids = fields.Many2many('account.journal', string="Diarios Exógena")
