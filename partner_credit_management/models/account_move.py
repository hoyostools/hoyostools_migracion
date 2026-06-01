from odoo import models, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        self._check_partner_credit_blocked()
        return super().write(vals)

    @api.constrains('partner_id')
    def _check_partner_credit_blocked(self):
        for move in self:
            if move.partner_id.credit_blocked:
                raise ValidationError(_(
                    "Este cliente se encuentra bloqueado. "
                    "Por favor contacte al área de cartera."
                ))