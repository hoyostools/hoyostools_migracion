from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        partner = self.env['res.partner'].browse(vals.get('partner_id'))
        if partner:
            if not partner.validate_transaction_limits_p or (partner.purchase_limit and partner.purchase_total_current_period + vals.get('amount_total', 0) > partner.purchase_limit):
                raise ValidationError(_(
                    "El proveedor {} ha superado el tope de compras para el período definido.".format(partner.name)
                ))
        return super(PurchaseOrder, self).create(vals)