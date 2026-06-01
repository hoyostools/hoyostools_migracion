from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class MultiInvoicePaymentWizard(models.TransientModel):
    _name = 'multi.invoice.payment.wizard'
    _description = 'Pago múltiple de facturas'

    payment_date = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.context_today,
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    difference_amount = fields.Monetary(
        string='Diferencia en pago',
        compute='_compute_difference_amount',
        currency_field='currency_id',
        store=False,
    )

    journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        required=True,
        domain=[('type', 'in', ('bank', 'cash'))],
    )

    payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string='Método de Pago',
        required=True,
        domain="""
            [
                ('journal_id', '=', journal_id),
                ('payment_type', '=', payment_type)
            ]
        """
    )

    payment_type = fields.Selection(
        [
            ('inbound', 'Recibir'),
            ('outbound', 'Enviar')
        ],
        string='Tipo de pago',
        default='inbound',
        required=True,
    )

    line_ids = fields.One2many(
        'multi.invoice.payment.wizard.line',
        'wizard_id',
        string='Líneas',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        active_ids = self.env.context.get('active_ids', [])

        invoices = self.env['account.move'].browse(active_ids).filtered(
            lambda m:
                m.is_invoice(include_receipts=True)
                and m.state == 'posted'
                and m.payment_state in ('not_paid', 'partial')
        )

        line_vals = []

        for move in invoices:

            line_vals.append((0, 0, {
                'move_id': move.id,
                'move_id_int': move.id,

                'partner_id': move.partner_id.id,
                'partner_id_int': move.partner_id.id,

                'invoice_amount': move.amount_total,
                'residual_amount': move.amount_residual,
                'receive_amount': move.amount_residual,
            }))

        res['line_ids'] = line_vals

        return res

    @api.depends('line_ids.receive_amount')
    def _compute_difference_amount(self):

        for wizard in self:
            total_receive = sum(
                wizard.line_ids.mapped('receive_amount')
            )

            total_residual = sum(
                wizard.line_ids.mapped('invoice_amount')
            )

            wizard.difference_amount = (
                    total_residual - total_receive
            )

    @api.onchange('journal_id', 'payment_type')
    def _onchange_journal_payment_type(self):

        self.payment_method_line_id = False

        methods = self.env['account.payment.method.line']

        if self.journal_id:

            if self.payment_type == 'inbound':

                methods = (
                    self.journal_id
                    .inbound_payment_method_line_ids
                )

            elif self.payment_type == 'outbound':

                methods = (
                    self.journal_id
                    .outbound_payment_method_line_ids
                )

        return {
            'domain': {
                'payment_method_line_id': [
                    ('id', 'in', methods.ids)
                ]
            }
        }

    def action_validate(self):
        self.ensure_one()

        _logger.warning("========== INICIO ACTION VALIDATE ==========")

        payments = self.env['account.payment']

        grouped = {}

        for line in self.line_ids:

            if not line.move_id_int:
                continue

            if line.receive_amount <= 0:
                continue

            partner_id = line.partner_id_int

            if partner_id not in grouped:
                grouped[partner_id] = {
                    'amount': 0.0,
                    'invoice_ids': [],
                }

            grouped[partner_id]['amount'] += line.receive_amount
            grouped[partner_id]['invoice_ids'].append(
                line.move_id_int
            )

        _logger.warning(
            "CLIENTES AGRUPADOS: %s",
            grouped
        )

        if not grouped:
            raise ValidationError(
                _("No hay líneas válidas.")
            )

        for partner_id, data in grouped.items():

            partner = self.env['res.partner'].browse(
                partner_id
            ).commercial_partner_id

            amount = data['amount']

            _logger.warning("""
    CLIENTE: %s
    MONTO: %s
    FACTURAS: %s
    """,
                partner.display_name,
                amount,
                data['invoice_ids']
            )

            payment_vals = {
                'partner_id': partner.id,
                'partner_type': (
                    'customer'
                    if self.payment_type == 'inbound'
                    else 'supplier'
                ),
                'payment_type': self.payment_type,
                'amount': amount,
                'date': self.payment_date,
                'journal_id': self.journal_id.id,
                'payment_method_line_id':
                    self.payment_method_line_id.id,
                'voucher_type': 'pago',
            }

            payment = self.env[
                'account.payment'
            ].create(payment_vals)

            _logger.warning(
                "PAGO CREADO ID: %s",
                payment.id
            )

            if (
                hasattr(payment, 'vendor_id')
                and partner.user_id
            ):
                payment.vendor_id = partner.user_id.id

            payment.action_post()

            # ==========================================
            # LINEA CONTABLE DEL PAGO
            # ==========================================

            payment_line = payment.move_id.line_ids.filtered(
                lambda l:
                    l.account_id.account_type == 'asset_receivable'
                    and not l.reconciled
            )

            payment_line = payment_line[:1]

            # ==========================================
            # CONCILIACION PARCIAL POR FACTURA
            # ==========================================

            for wizard_line in self.line_ids.filtered(
                lambda l:
                    l.partner_id_int == partner_id
                    and l.receive_amount > 0
            ):

                invoice = self.env['account.move'].browse(
                    wizard_line.move_id_int
                )

                invoice_line = invoice.line_ids.filtered(
                    lambda l:
                        l.account_id.account_type == 'asset_receivable'
                        and not l.reconciled
                )[:1]

                if not invoice_line:
                    continue

                amount_to_reconcile = wizard_line.receive_amount

                amount_to_reconcile = min(
                    abs(amount_to_reconcile),
                    abs(invoice_line.amount_residual),
                    abs(payment_line.amount_residual),
                )

                _logger.warning("""
                CONCILIANDO

                FACTURA: %s
                INVOICE LINE: %s
                PAYMENT LINE: %s
                MONTO: %s
                """,
                    invoice.name,
                    invoice_line.id,
                    payment_line.id,
                    amount_to_reconcile
                )

                partial_vals = {
                    'debit_move_id': invoice_line.id,
                    'credit_move_id': payment_line.id,
                    'amount': amount_to_reconcile,
                }

                # Misma moneda
                if invoice_line.currency_id and payment_line.currency_id:
                    partial_vals.update({
                        'debit_amount_currency': amount_to_reconcile,
                        'credit_amount_currency': amount_to_reconcile,
                    })

                _logger.warning(
                    "PARTIAL VALS: %s",
                    partial_vals
                )

                self.env['account.partial.reconcile'].create(
                    partial_vals
                )
         
            payments |= payment

        _logger.warning(
            "PAGOS CREADOS FINAL: %s",
            payments.ids
        )

        if not payments:
            raise ValidationError(
                _("No se crearon pagos.")
            )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Pagos'),
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', payments.ids)],
        }

class MultiInvoicePaymentWizardLine(models.TransientModel):
    _name = 'multi.invoice.payment.wizard.line'
    _description = 'Línea pago múltiple'

    wizard_id = fields.Many2one(
        'multi.invoice.payment.wizard',
        string='Wizard',
        ondelete='cascade',
    )

    move_id = fields.Many2one(
        'account.move',
        string='Factura',
    )

    move_id_int = fields.Integer(
        string='Move ID'
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
    )

    partner_id_int = fields.Integer(
        string='Partner ID'
    )

    invoice_amount = fields.Monetary(
        string='Monto Factura',
        currency_field='currency_id',
    )

    residual_amount = fields.Monetary(
        string='Monto restante',
        compute='_compute_residual_amount',
        currency_field='currency_id',
        store=False
    )

    receive_amount = fields.Monetary(
        string='Recibir Monto',
        currency_field='currency_id',
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    @api.depends(
        'invoice_amount',
        'receive_amount'
    )
    def _compute_residual_amount(self):

        for line in self:

            line.residual_amount = (
                line.invoice_amount
                - line.receive_amount
            )