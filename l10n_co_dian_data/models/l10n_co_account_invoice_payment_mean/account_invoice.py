# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):
	_inherit = "account.move"

	def _get_zzz(self):
		zz_id = False
		if self.sudo().env['ir.model'].search([('model','=','account.payment.mean.code')]):
			zz_id = self.env['account.payment.mean.code'].search([('code','=','ZZZ')])
		if zz_id:
			return zz_id.id
		return False

	payment_mean_id = fields.Many2one(
		comodel_name='account.payment.mean',
		string='Payment Method',
		copy=False,
		default=False)

	payment_mean_code_id = fields.Many2one('account.payment.mean.code',
		string='Mean of Payment',
		copy=False,
		default=_get_zzz)
 
	#invoice_date = fields.Date(
	#	default=fields.Date.today())
 
