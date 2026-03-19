# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _

class PurchaseOrderLine(models.Model):

	_inherit = 'purchase.order.line'

	vendor_price = fields.Float(string="Vendor Price")
	delivery_date = fields.Date(string="Delivery Date")
	description = fields.Char(string="Vendor Message")
	user_change = fields.Many2one('res.users', string="Confirma", default=lambda self: self.env.user)
	can_update = fields.Boolean(string="Can Update", default=True)



