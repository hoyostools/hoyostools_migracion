from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        res = super(PurchaseOrder, self)._prepare_sale_order_data(name, partner, company, direct_delivery_address)
        res['b4b'] = True
        return res


