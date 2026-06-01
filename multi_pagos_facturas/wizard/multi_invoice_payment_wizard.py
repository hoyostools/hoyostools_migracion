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

        payments_created = self.env['account.payment']

        grouped = {}

        for line in self.line_ids:
            _logger.warning("""
    LINEA:
        move_id_int=%s
        partner_id_int=%s
        receive_amount=%s
    """,
                line.move_id_int,
                line.partner_id_int,
                line.receive_amount
            )

            if not line.move_id_int:
                continue

            if line.receive_amount <= 0:
                continue

            partner_id = line.partner_id_int

            if partner_id not in grouped:
                grouped[partner_id] = {
                    'amount': 0.0,
                    'invoice_ids': [],
                    'partner_id': partner_id,
                }

            grouped[partner_id]['amount'] += line.receive_amount
            grouped[partner_id]['invoice_ids'].append(line.move_id_int)

        _logger.warning("CLIENTES AGRUPADOS: %s", grouped)

        if not grouped:
            raise ValidationError("No hay líneas válidas.")

        for partner_id, data in grouped.items():

            amount = data['amount']
            invoice_ids = data['invoice_ids']

            _logger.warning("""
    CLIENTE: %s
    FACTURAS: %s
    TOTAL PAGO: %s
    """,
                partner_id,
                invoice_ids,
                amount
            )

            invoices = self.env['account.move'].browse(invoice_ids)

            _logger.warning(
                "FACTURAS ENCONTRADAS: %s",
                invoices.ids
            )

            if not invoices:
                _logger.warning("NO ENCONTRO FACTURAS")
                continue

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
                })

                _logger.warning(
                    "WIZARD REGISTER ID: %s",
                    register_wizard.id
                )

                _logger.warning(
                    "MONTO ORIGINAL WIZARD: %s",
                    register_wizard.amount
                )

                register_wizard.amount = amount

                _logger.warning(
                    "MONTO DESPUES DE ASIGNAR: %s",
                    register_wizard.amount
                )

                result = register_wizard.action_create_payments()

                _logger.warning(
                    "RESULTADO ACTION_CREATE_PAYMENTS: %s",
                    result
                )

                payments = self.env['account.payment'].search(
                    [('partner_id', '=', partner_id)],
                    order='id desc',
                    limit=10
                )

                _logger.warning(
                    "PAGOS ENCONTRADOS: %s",
                    payments.ids
                )

                if payments:
                    payment = payments[0]

                    _logger.warning(
                        "PAGO SELECCIONADO: %s",
                        payment.id
                    )

                    partner = invoices[0].partner_id.commercial_partner_id

                    if hasattr(payment, 'vendor_id') and partner.user_id:
                        payment.vendor_id = partner.user_id.id

                    payments_created |= payment

            except Exception as e:
                _logger.exception(
                    "ERROR CREANDO PAGO CLIENTE %s",
                    partner_id
                )

        _logger.warning(
            "PAGOS CREADOS FINAL: %s",
            payments_created.ids
        )

        if not payments_created:
            raise ValidationError("No se crearon pagos.")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Pagos',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', payments_created.ids)],
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