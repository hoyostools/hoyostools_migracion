# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def _create_invoices(self, sale_orders):
        invoices = super()._create_invoices(sale_orders)
        for invoice in invoices:
            if invoice.line_ids.sale_line_ids.order_id.payment_term_id.account_payment_mean:
                payment_mean_id = invoice.line_ids.sale_line_ids.order_id.payment_term_id.account_payment_mean
                invoice.payment_mean_id = payment_mean_id
        return invoices
