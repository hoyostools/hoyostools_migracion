from odoo import models, fields, api, _
from odoo.exceptions import UserError
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

        valid_lines = self.line_ids.filtered(
            lambda l: l.move_id_int and l.receive_amount > 0
        )

        if not valid_lines:
            raise UserError(_('No hay líneas válidas.'))

        # =====================================================
        # AGRUPAR LINEAS POR CLIENTE
        # =====================================================

        grouped_lines = {}

        for line in valid_lines:

            partner_id = line.partner_id_int

            if partner_id not in grouped_lines:
                grouped_lines[partner_id] = {
                    'amount': 0.0,
                    'invoice_ids': [],
                    'partner_id': partner_id,
                }

            grouped_lines[partner_id]['amount'] += line.receive_amount
            grouped_lines[partner_id]['invoice_ids'].append(
                line.move_id_int
            )

        _logger.warning(
            "CLIENTES AGRUPADOS: %s",
            grouped_lines
        )

        # =====================================================
        # CREAR UN PAGO POR CLIENTE
        # =====================================================

        for partner_id, data in grouped_lines.items():

            invoices = self.env['account.move'].browse(
                data['invoice_ids']
            )

            if not invoices:
                continue

            amount = data['amount']

            _logger.warning("""
                CLIENTE: %s
                FACTURAS: %s
                TOTAL PAGO: %s
            """,
                partner_id,
                invoices.ids,
                amount,
            )

            try:

                register_wizard = self.env[
                    'account.payment.register'
                ].with_context(
                    active_model='account.move',
                    active_ids=invoices.ids,
                ).create({
                    'payment_date': self.payment_date,
                    'journal_id': self.journal_id.id,
                    'payment_method_line_id': self.payment_method_line_id.id,
                    'amount': amount,
                })

                register_wizard.action_create_payments()

                payment = self.env['account.payment'].search(
                    [
                        (
                            'partner_id',
                            '=',
                            invoices[0].partner_id.commercial_partner_id.id
                        ),
                        ('amount', '=', amount),
                    ],
                    order='id desc',
                    limit=1
                )

                if payment:

                    payment.vendor_id = (
                        invoices[0]
                        .partner_id
                        .commercial_partner_id
                        .user_id
                        .id
                    )

                    payments |= payment

                    _logger.warning(
                        "PAGO CREADO: %s",
                        payment.id
                    )

            except Exception as e:

                _logger.exception("""
                    ERROR CREANDO PAGO
                    CLIENTE: %s
                    ERROR: %s
                """,
                    partner_id,
                    str(e)
                )

        if not payments:
            raise UserError(_('No se crearon pagos.'))

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