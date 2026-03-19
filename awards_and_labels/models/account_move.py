from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    bandera = fields.Boolean(
        string='Bandera',
        readonly=True,
    )