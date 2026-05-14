from odoo import models, fields

class AccountTax(models.Model):
    _inherit = 'account.tax'

    base_check = fields.Boolean(string='¿Aplicable con base?')
    reteiva = fields.Boolean(string='¿Aplica reteiva?')
    base_amount = fields.Float(string='Valor base')
    impuesto_reteiva = fields.Many2one('account.tax',string='Impuesto reteiva')
