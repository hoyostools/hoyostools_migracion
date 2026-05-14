from odoo import fields, models


class AccountFiscalPosition(models.Model):
	_inherit = 'account.fiscal.position'

	aplica_reteiva = fields.Boolean('Aplica reteiva')