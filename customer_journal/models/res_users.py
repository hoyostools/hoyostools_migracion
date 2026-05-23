from odoo import _, api, models, fields


class ResUser(models.Model):
    _inherit = "res.users"

    account_journal_ids = fields.Many2many('account.journal', string="Diarios habilitados")
    has_group_restriction = fields.Boolean(string="Habilitados", compute='_has_group_restriction')

    def _has_group_restriction(self):
        for record in self:
            if record.has_group('customer_journal.group_restricted_journal'):
                record.has_group_restriction = True
            else:
                record.has_group_restriction = False


