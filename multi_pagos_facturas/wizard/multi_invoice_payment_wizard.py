from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MultiInvoicePaymentWizard(models.TransientModel):
    _name = 'multi.invoice.payment.wizard'
    _description = 'Pago de Facturas Multiples'

    journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        domain="[('type', 'in', ('bank', 'cash'))]",
        required=True
    )

    payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string='Metodo de Pago',
        required=True,
    )

    payment_date = fields.Date(
        string='Fecha',
        default=fields.Date.context_today,
        required=True
    )

    difference_amount = fields.Monetary(
        string='Diferencia en pago',
        compute='_compute_difference_amount',
        currency_field='currency_id',
        store=False
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    line_ids = fields.One2many(
        'multi.invoice.payment.wizard.line',
        'wizard_id',
        string='Facturas'
    )

    @api.depends('line_ids.receive_amount')
    def _compute_difference_amount(self):
        for wizard in self:
            total_residual = sum(
                wizard.line_ids.mapped('residual_amount')
            )

            total_receive = sum(
                wizard.line_ids.mapped('receive_amount')
            )

            wizard.difference_amount = total_residual - total_receive

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.payment_method_line_id = False

        return {
            'domain': {
                'payment_method_line_id': [
                    ('id', 'in', self.journal_id.inbound_payment_method_line_ids.ids)
                ]
            }
        }

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        active_ids = self.env.context.get('active_ids', [])

        invoices = self.env['account.move'].browse(active_ids).filtered(
            lambda m: m.move_type == 'out_invoice' and m.state == 'posted'
        )

        lines = []

        for invoice in invoices:
            lines.append((0, 0, {
                'move_id': invoice.id,
                'partner_id': invoice.partner_id.id,
                'invoice_amount': invoice.amount_total,
                'residual_amount': invoice.amount_residual_signed,
                'receive_amount': invoice.amount_residual_signed,
            }))

        res['line_ids'] = lines

        return res

    def action_validate(self):

        if not self.line_ids:
            raise UserError(_('No hay lineas para procesar.'))

        grouped_lines = defaultdict(list)

        for line in self.line_ids:
            if line.receive_amount <= 0:
                continue

            grouped_lines[line.partner_id.id].append(line)

        for partner_id, lines in grouped_lines.items():

            partner = self.env['res.partner'].browse(partner_id)

            total_amount = sum(lines.mapped('receive_amount'))

            invoices = lines.mapped('move_id')

            payment_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': partner.id,
                'amount': total_amount,
                'date': self.payment_date,
                'journal_id': self.journal_id.id,
                'payment_method_line_id': self.payment_method_line_id.id,
            }

            payment = self.env['account.payment'].create(payment_vals)

            payment.action_post()

            receivable_lines = payment.move_id.line_ids.filtered(
                lambda l: l.account_type == 'asset_receivable'
            )

            invoice_lines = invoices.line_ids.filtered(
                lambda l: (
                    l.account_type == 'asset_receivable'
                    and not l.reconciled
                )
            )

            # reconciliacion parcial
            for wizard_line in lines:

                invoice = wizard_line.move_id

                invoice_receivable = invoice.line_ids.filtered(
                    lambda l: (
                        l.account_type == 'asset_receivable'
                        and not l.reconciled
                    )
                )

                amount_to_reconcile = wizard_line.receive_amount

                partial_lines = (
                    receivable_lines + invoice_receivable
                )

                partial_lines.with_context(
                    amount=amount_to_reconcile
                ).reconcile()

        return {'type': 'ir.actions.act_window_close'}


class MultiInvoicePaymentWizardLine(models.TransientModel):
    _name = 'multi.invoice.payment.wizard.line'
    _description = 'Lineas Pago Multiple'

    wizard_id = fields.Many2one(
        'multi.invoice.payment.wizard'
    )

    move_id = fields.Many2one(
        'account.move',
        string='Factura'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente'
    )

    invoice_amount = fields.Monetary(
        string='Monto Factura',
        currency_field='currency_id'
    )

    residual_amount = fields.Monetary(
        string='Monto Restante',
        currency_field='currency_id'
    )

    receive_amount = fields.Monetary(
        string='Recibir Monto',
        currency_field='currency_id'
    )

    remaining_amount = fields.Monetary(
        string='Monto restante',
        compute='_compute_remaining_amount',
        currency_field='currency_id',
        store=False
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='wizard_id.currency_id'
    )

    @api.depends('residual_amount', 'receive_amount')
    def _compute_remaining_amount(self):
        for line in self:
            line.remaining_amount = (
                line.residual_amount - line.receive_amount
            )