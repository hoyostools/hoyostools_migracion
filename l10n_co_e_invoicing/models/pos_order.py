from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.depends('account_move')
    def _generate_pos_order_invoice(self):
        res = super()._generate_pos_order_invoice()
        for record in self:
            record.account_move.compute_electronic_invoice()
        return res

    def _create_invoice(self, move_vals):
        res = super()._create_invoice(move_vals)
        if self.payment_ids.payment_method_id.account_payment_mean:
            res.payment_mean_id = self.payment_ids.payment_method_id.account_payment_mean[0]
        return res
