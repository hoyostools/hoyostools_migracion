from odoo import models, fields

class AccountTax(models.Model):
    _inherit = 'account.tax'

    base_check = fields.Boolean(string='¿Aplicable con base?')
    base_amount = fields.Float(string='Valor base')
