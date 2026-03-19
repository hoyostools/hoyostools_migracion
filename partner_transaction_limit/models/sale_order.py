from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        partner = self.env['res.partner'].browse(vals.get('partner_id'))
        if partner:
            if not partner.validate_transaction_limits or (partner.sales_limit and partner.sales_total_current_period + vals.get('amount_total', 0) > partner.sales_limit):
                raise ValidationError(_(
                    "El cliente {} ha superado el tope de ventas para el período definido.".format(partner.name)
                ))
        return super(SaleOrder, self).create(vals)
