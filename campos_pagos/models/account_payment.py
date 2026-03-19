from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import os
from datetime import datetime
import base64


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    vendor_id = fields.Many2one("res.users", string="Vendedor", help="Vendedor del tercero.")

    @api.onchange('partner_id')
    def _onchange_vendor_id(self):
        for record in self:
            if record.partner_id and record.partner_id.user_id:
                record.vendor_id = record.partner_id.user_id
            if record.partner_id and not record.partner_id.user_id:
                record.vendor_id = False