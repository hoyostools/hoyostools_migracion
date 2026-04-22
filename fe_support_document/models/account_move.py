from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        if vals.get('move_type') == 'in_refund':
            vals['refund_type'] = 'credit'
        return super().create(vals)
