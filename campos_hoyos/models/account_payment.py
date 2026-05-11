from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.payment'

    comentario = fields.Char(string='Comentario')