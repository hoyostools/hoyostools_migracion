from odoo import api, fields, models

class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    is_account = fields.Boolean(string="Exogena")
    custom_partner_name = fields.Char(string='Exogen Partner Name', readonly=True)
