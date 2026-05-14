from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def take_payment_receipt_data(self):

        for payment in self:

            data_table = []
            amount_residual = []

            for invoice in payment.reconciled_invoice_ids:

                row = [
                    invoice.date,
                    invoice.display_name,
                    "{:,.2f}".format(invoice.amount_total)
                ]

                if row not in data_table:
                    data_table.append(row)

                for matched_credit_id in invoice.line_ids.filtered(
                    lambda line: line.display_type == 'payment_term'
                ).matched_credit_ids:

                    row = [
                        matched_credit_id.credit_move_id.date,
                        matched_credit_id.credit_move_id.move_name,
                        "{:,.2f}".format(
                            matched_credit_id.credit_move_id.amount_currency
                        )
                    ]

                    if row not in data_table:
                        data_table.append(row)

                if invoice.amount_residual:

                    row = [
                        invoice.display_name,
                        invoice.amount_residual
                    ]

                    if row not in amount_residual:
                        amount_residual.append(row)

            for invoice in payment.reconciled_bill_ids:

                row = [
                    invoice.date,
                    invoice.display_name,
                    "{:,.2f}".format(invoice.amount_total)
                ]

                if row not in data_table:
                    data_table.append(row)

                for matched_credit_id in invoice.line_ids.filtered(
                    lambda line: line.display_type == 'payment_term'
                ).matched_credit_ids:

                    row = [
                        matched_credit_id.credit_move_id.date,
                        matched_credit_id.credit_move_id.move_name,
                        "{:,.2f}".format(
                            matched_credit_id.credit_move_id.amount_currency
                        )
                    ]

                    if row not in data_table:
                        data_table.append(row)

                if invoice.amount_residual:

                    row = [
                        invoice.display_name,
                        invoice.amount_residual
                    ]

                    if row not in amount_residual:
                        amount_residual.append(row)

            return data_table, amount_residual