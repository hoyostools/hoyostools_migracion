import logging
import uuid
from datetime import date, timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare, float_is_zero

_logger = logging.getLogger(__name__)


class SemiAutoReconciliationSupplierLine(models.TransientModel):
    _name = 'semi.auto.reconciliation.supplier.line'
    _description = 'Línea de conciliación semiautomática proveedores'

    partner_id = fields.Many2one('res.partner', string='Proveedor')
    invoice_date = fields.Date(related='move_id.invoice_date', string='Fecha Factura', store=True)
    move_id = fields.Many2one('account.move', string='Factura / Nota crédito')
    invoice_payment_term_id = fields.Many2one('account.payment.term', related='move_id.invoice_payment_term_id', string='Término de Pago', store=True)
    date = fields.Date(related='payment_id.date', string='Fecha Pago', store=True)
    payment_id = fields.Many2one('account.payment', string='Pago')
    due_date = fields.Date(string='Fecha Vencimiento', compute='_compute_due_date', store=True)
    is_due = fields.Boolean(compute='_compute_due_status', store=False)
    is_warning_due = fields.Boolean(compute='_compute_due_status', store=False)
    document_type = fields.Selection([('invoice', 'Factura'),('credit_note', 'Nota de Crédito'),('payment', 'Pago'),], string='Tipo', required=True)
    reconcile_full = fields.Boolean(string='Conciliar Todo')
    debit = fields.Monetary(string='Débito')
    credit = fields.Monetary(string='Crédito')
    amount_to_apply = fields.Monetary(string='Aplicar', compute='_compute_amount_to_apply', inverse='_inverse_amount_to_apply', store=True, default=0.0)
    currency_id = fields.Many2one('res.currency', string='Moneda')
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, readonly=True)
    journal_id = fields.Many2one('account.journal', string='Diario')
    discount = fields.Monetary(string='Descuento Financiero', compute='_compute_discount')
    
    def _compute_discount(self):

        for record in self:
            record.discount = 0.0
            if (
                record.due_date
                and record.move_id
                and record.invoice_payment_term_id
            ):
                if record.due_date > date.today():
                    discount_pct = (
                        record.invoice_payment_term_id.discount_percentage
                        or 0.0
                    )
                    record.discount = (
                        record.move_id.amount_untaxed
                        * (discount_pct / 100)
                    )

    @api.depends('due_date')
    def _compute_due_status(self):
        today = date.today()
        warning_limit = today + timedelta(days=5)

        for rec in self:
            rec.is_due = rec.due_date and rec.due_date <= today
            rec.is_warning_due = (
                rec.due_date
                and today < rec.due_date <= warning_limit
            )

    @api.depends('move_id')
    def _compute_due_date(self):
        for rec in self:
            rec.due_date = (
                rec.move_id.invoice_date_due
                if rec.move_id
                else False
            )

    @api.constrains('amount_to_apply')
    def _check_amount_to_apply_sign(self):
        precision = self.env[
            'decimal.precision'
        ].precision_get('Account')

        for rec in self:
            if (
                rec.document_type == 'invoice'
                and float_compare(
                    rec.amount_to_apply,
                    0.0,
                    precision_digits=precision
                ) < 0
            ):
                raise ValidationError(
                    'Para facturas, el monto a aplicar debe ser positivo.'
                )

            if (
                rec.document_type in ['credit_note', 'payment']
                and float_compare(
                    rec.amount_to_apply,
                    0.0,
                    precision_digits=precision
                ) > 0
            ):
                raise ValidationError(
                    'Para pagos o notas crédito, el monto debe ser negativo.'
                )

    @api.onchange('amount_to_apply')
    def _onchange_amount_to_apply(self):

        precision = self.env[
            'decimal.precision'
        ].precision_get('Account')

        if (
            self.debit
            and float_compare(
                self.amount_to_apply,
                (self.debit - self.discount),
                precision_digits=precision
            ) > 0
        ):

            self.amount_to_apply = (
                self.debit - self.discount
            )

        elif (
            self.credit
            and float_compare(
                abs(self.amount_to_apply),
                self.credit,
                precision_digits=precision
            ) > 0
        ):

            self.amount_to_apply = -self.credit

    @api.depends('reconcile_full', 'debit', 'credit', 'document_type', 'discount')
    def _compute_amount_to_apply(self):

        for rec in self:
            if rec.reconcile_full:
                if rec.document_type == 'invoice':

                    rec.amount_to_apply = (
                        rec.debit - rec.discount
                    )
                elif rec.document_type in [
                    'credit_note',
                    'payment'
                ]:
                    rec.amount_to_apply = -rec.credit
                else:
                    rec.amount_to_apply = 0.0

    def _inverse_amount_to_apply(self):
        pass

    @api.model
    def load_documents_for_due_range(self, date_due_from, date_due_to):
        self.search([]).unlink()

        journal = self.env['account.journal'].search([
            ('name', '=', 'Cruce Proveedores')
        ], limit=1)

        if not journal:
            raise UserError(
                'No existe un diario llamado "Cruce Proveedores".'
            )

        invoices = self.env['account.move'].search([
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
            ('amount_residual', '>', 0),
            ('invoice_date_due', '>=', date_due_from),
            ('invoice_date_due', '<=', date_due_to),
        ])

        credit_notes = self.env['account.move'].search([
            ('move_type', '=', 'in_refund'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
            ('amount_residual', '>', 0),
        ])

        supplier_ids = list(set(
            invoices.mapped('partner_id.commercial_partner_id.id')
            + credit_notes.mapped('partner_id.commercial_partner_id.id')
        ))

        payments = self.env['account.payment'].search([
            ('state', '=', 'posted'),
            ('payment_type', '=', 'outbound'),
            ('partner_id.commercial_partner_id', 'in', supplier_ids),
            ('move_id.line_ids.account_id.account_type', '=', 'liability_payable'),
            ('move_id.line_ids.reconciled', '=', False),
        ])

        payment_partners = set(
            payments.mapped('partner_id.commercial_partner_id.id')
        )
        invoice_partners = set(
            invoices.mapped('partner_id.commercial_partner_id.id')
        )
        credit_note_partners = set(
            credit_notes.mapped('partner_id.commercial_partner_id.id')
        )

        valid_partners = invoice_partners & (
            payment_partners | credit_note_partners
        )

        if not valid_partners:
            raise UserError(
                'No se encontraron proveedores con facturas y pagos o notas crédito disponibles.'
            )

        partners = self.env['res.partner'].browse(list(valid_partners))

        for partner in partners:
            related_ids = [partner.id] + partner.child_ids.ids
            lines = []

            for inv in invoices.filtered(
                lambda i: i.partner_id.commercial_partner_id.id == partner.id
            ):
                lines.append({
                    'partner_id': partner.id,
                    'move_id': inv.id,
                    'document_type': 'invoice',
                    'debit': inv.amount_residual,
                    'credit': 0.0,
                    'amount_to_apply': 0.0,
                    'currency_id': inv.currency_id.id,
                    'company_id': inv.company_id.id,
                    'journal_id': journal.id,
                })

            for cr in credit_notes.filtered(
                lambda c: c.partner_id.commercial_partner_id.id == partner.id
            ):
                lines.append({
                    'partner_id': partner.id,
                    'move_id': cr.id,
                    'document_type': 'credit_note',
                    'debit': 0.0,
                    'credit': cr.amount_residual,
                    'amount_to_apply': 0.0,
                    'currency_id': cr.currency_id.id,
                    'company_id': cr.company_id.id,
                    'journal_id': journal.id,
                })

            for pay in payments.filtered(
                lambda p: p.partner_id.commercial_partner_id.id == partner.id
            ):
                payable_line = pay.move_id.line_ids.filtered(
                    lambda l: (
                        l.account_id.account_type == 'liability_payable'
                        and not l.reconciled
                        and not float_is_zero(
                            l.amount_residual,
                            precision_digits=self.env[
                                'decimal.precision'
                            ].precision_get('Account')
                        )
                    )
                )

                if payable_line:
                    lines.append({
                        'partner_id': partner.id,
                        'payment_id': pay.id,
                        'document_type': 'payment',
                        'debit': 0.0,
                        'credit': abs(payable_line[0].amount_residual),
                        'amount_to_apply': 0.0,
                        'currency_id': pay.currency_id.id,
                        'company_id': pay.company_id.id,
                        'journal_id': journal.id,
                    })

            if (
                any(l['debit'] > 0 for l in lines)
                and any(l['credit'] > 0 for l in lines)
            ):
                self.create(lines)

    @api.model
    def action_reconcile_selected(self, ids):
        lines = self.browse(ids)

        if not lines:
            raise UserError('No se seleccionaron líneas.')

        precision = self.env[
            'decimal.precision'
        ].precision_get('Account')

        grouped_by_partner = {}

        for line in lines:
            if float_is_zero(
                line.amount_to_apply,
                precision_digits=precision
            ):
                raise UserError(
                    'El monto a aplicar no puede ser cero.'
                )

            if line.document_type == 'invoice' and line.amount_to_apply < 0:
                raise UserError(
                    f'Para facturas, el monto debe ser positivo: {line.move_id.name}'
                )

            if (
                line.document_type in ['payment', 'credit_note']
                and line.amount_to_apply > 0
            ):
                raise UserError(
                    'Para pagos/notas crédito, el monto debe ser negativo.'
                )

            grouped_by_partner.setdefault(
                line.partner_id.id,
                []
            ).append(line)

        def _get_open_payable_line_from_move(move):
            aml = move.line_ids.filtered(
                lambda l: (
                    l.account_id.account_type == 'liability_payable'
                    and not float_is_zero(
                        l.amount_residual,
                        precision_digits=precision
                    )
                )
            )
            return aml[:1]

        def _get_payment_nc_date(wl):
            if wl.document_type == 'payment':
                return wl.payment_id.date

            if wl.document_type == 'credit_note':
                return wl.move_id.date or wl.move_id.invoice_date

            return False

        journal = self.env['account.journal'].search([
            ('name', '=', 'Cruce Proveedores')
        ], limit=1)

        if not journal:
            raise UserError(
                'No existe un diario llamado "Cruce Proveedores".'
            )

        if journal.type not in ('bank', 'cash'):
            raise UserError(
                'El diario "Cruce Proveedores" debe ser tipo Banco o Caja.'
            )

        clearing_account = journal.default_account_id

        if not clearing_account:
            raise UserError(
                'El diario "Cruce Proveedores" debe tener cuenta por defecto.'
            )

        payment_method_line = journal.outbound_payment_method_line_ids[:1]

        if not payment_method_line:
            raise UserError(
                'El diario "Cruce Proveedores" no tiene método de pago de salida.'
            )

        for partner_id, partner_lines in grouped_by_partner.items():
            invoice_lines = [
                l for l in partner_lines
                if l.document_type == 'invoice'
            ]

            payment_nc_lines = [
                l for l in partner_lines
                if l.document_type in ('payment', 'credit_note')
            ]

            if not payment_nc_lines:
                raise UserError(
                    'Debe seleccionar al menos un pago o nota crédito.'
                )

            total_invoices = sum(
                l.amount_to_apply for l in invoice_lines
            )

            total_credits = sum(
                abs(l.amount_to_apply) for l in payment_nc_lines
            )

            if float_compare(
                total_invoices,
                total_credits,
                precision_digits=precision
            ) != 0:
                raise UserError(
                    f'El total de facturas ({total_invoices}) no coincide '
                    f'con pagos/NC ({total_credits}).'
                )

            # groups_by_date = {}

            # for l in payment_nc_lines:
            #     d = _get_payment_nc_date(l)

            #     if not d:
            #         raise UserError(
            #             'No se pudo determinar la fecha del documento.'
            #         )

            #     groups_by_date.setdefault(d, []).append(l)

            # sorted_dates = sorted(groups_by_date.keys())

            invoice_queue = sorted(
                invoice_lines,
                key=lambda x: (
                    x.move_id.invoice_date_due
                    or x.move_id.invoice_date
                    or x.move_id.date
                    or fields.Date.today(),
                    x.move_id.name or '',
                    x.id,
                )
            )

            invoice_remaining = {
                l.id: l.amount_to_apply for l in invoice_queue
            }

            def _process_single_cruce(cruce_date, normalized_lines):
                debit_total = 0.0
                credit_total = 0.0

                for item in normalized_lines:
                    amount = item['amount']

                    if amount > 0:
                        debit_total += amount
                    else:
                        credit_total += abs(amount)

                if float_compare(
                    debit_total,
                    credit_total,
                    precision_digits=precision
                ) != 0:
                    raise UserError(
                        'El débito y crédito no coinciden.'
                    )

                cruce_name = (
                    self.env['ir.sequence'].next_by_code(
                        'cruce.saldos.supplier'
                    )
                    or f'CRUP/{uuid.uuid4().hex[:6].upper()}'
                )

                payment_vals = {
                    'payment_type': 'outbound',
                    'partner_type': 'supplier',
                    'voucher_type': 'pago',
                    'partner_id': partner_id,
                    'amount': debit_total,
                    'date': fields.Datetime.now().date(),
                    'journal_id': journal.id,
                    'payment_method_line_id': payment_method_line.id,
                    'ref': f'Cruce {cruce_name}',
                }

                cruce_payment = self.env[
                    'account.payment'
                ].create(payment_vals)

                cruce_payment.action_post()

                pay_move = cruce_payment.move_id

                pay_payable_lines = pay_move.line_ids.filtered(
                    lambda l: (
                        l.account_id.account_type == 'liability_payable'
                        and not l.reconciled
                    )
                )

                if not pay_payable_lines:
                    raise UserError(
                        'No se encontró línea payable en el pago de cruce.'
                    )

                pay_payable_line = pay_payable_lines[0]

                bridge_line_vals = []
                total_bridge_payable = 0.0

                for item in normalized_lines:
                    if item['document_type'] == 'invoice':
                        continue

                    move = item['move']
                    orig_line = _get_open_payable_line_from_move(move)

                    if not orig_line:
                        raise UserError(
                            f'No se encontró línea payable abierta en {move.name}'
                        )

                    orig_line = orig_line[0]
                    amount = abs(item['amount'])

                    if float_is_zero(
                        amount,
                        precision_digits=precision
                    ):
                        continue

                    total_bridge_payable += amount

                    bridge_line_vals.append((0, 0, {
                        'name': item['label'],
                        'partner_id': partner_id,
                        'account_id': orig_line.account_id.id,
                        'debit': 0.0,
                        'credit': amount,
                    }))

                bridge_line_vals.append((0, 0, {
                    'name': f'Contrapartida liquidez {cruce_name}',
                    'partner_id': partner_id,
                    'account_id': clearing_account.id,
                    'debit': total_bridge_payable,
                    'credit': 0.0,
                }))

                bridge_move = self.env['account.move'].create({
                    'ref': f'Bridge {cruce_name}',
                    'journal_id': journal.id,
                    'move_type': 'entry',
                    'partner_id': partner_id,
                    'date': cruce_date,
                    'line_ids': bridge_line_vals,
                })

                bridge_move.action_post()

                bridge_payable_lines = bridge_move.line_ids.filtered(
                    lambda l: (
                        l.account_id.account_type == 'liability_payable'
                        and not l.reconciled
                    )
                )

                cruce = self.env[
                    'cruce.saldos.supplier'
                ].create({
                    'name': cruce_name,
                    'partner_id': partner_id,
                    'date': fields.Date.today(),
                    'total_amount': debit_total,
                    'move_id': pay_move.id,
                })

                cruce._sync_move_lines_from_move()

                for item in normalized_lines:
                    cruce.line_ids.create({
                        'cruce_id': cruce.id,
                        'move_id': item.get('move_id') or False,
                        'payment_id': item.get('payment_id') or False,
                        'document_type': item['document_type'],
                        'amount_applied': item['amount'],
                    })

                for item in normalized_lines:
                    if item['document_type'] != 'invoice':
                        continue

                    move = item['move']
                    inv_line = _get_open_payable_line_from_move(move)

                    if not inv_line:
                        continue

                    inv_line = inv_line[0]
                    amount = abs(item['amount'])

                    self.env['account.partial.reconcile'].create({
                        'debit_move_id': pay_payable_line.id,
                        'credit_move_id': inv_line.id,
                        'amount': amount,
                        'debit_amount_currency': amount,
                        'credit_amount_currency': amount,
                    })

                for item in normalized_lines:
                    if item['document_type'] == 'invoice':
                        continue

                    move = item['move']
                    orig_line = _get_open_payable_line_from_move(move)

                    if not orig_line:
                        continue

                    orig_line = orig_line[0]
                    amount = abs(item['amount'])

                    bridge_match = bridge_payable_lines.filtered(
                        lambda l: (
                            l.partner_id.id == partner_id
                            and float_compare(
                                l.credit,
                                amount,
                                precision_digits=precision
                            ) == 0
                            and l.name == item['label']
                        )
                    )

                    if not bridge_match:
                        bridge_match = bridge_payable_lines.filtered(
                            lambda l: (
                                l.partner_id.id == partner_id
                                and float_compare(
                                    l.credit,
                                    amount,
                                    precision_digits=precision
                                ) == 0
                            )
                        )

                    if not bridge_match:
                        raise UserError(
                            f'No se encontró línea crédito en el puente '
                            f'para conciliar {move.name}.'
                        )

                    bridge_line = bridge_match[0]

                    self.env['account.partial.reconcile'].create({
                        'debit_move_id': orig_line.id,
                        'credit_move_id': bridge_line.id,
                        'amount': amount,
                        'debit_amount_currency': amount,
                        'credit_amount_currency': amount,
                    })

                cruce_date = fields.Date.today()
                needed = total_credits
                normalized_lines = []

                for inv in invoice_queue:
                    if float_is_zero(needed, precision_digits=precision):
                        break

                    rem = invoice_remaining.get(inv.id, 0.0)

                    if float_is_zero(rem, precision_digits=precision):
                        continue

                    take = (
                        rem
                        if float_compare(rem, needed, precision_digits=precision) <= 0
                        else needed
                    )

                    invoice_remaining[inv.id] = rem - take
                    needed -= take

                    normalized_lines.append({
                        'document_type': 'invoice',
                        'move': inv.move_id,
                        'move_id': inv.move_id.id,
                        'payment_id': False,
                        'amount': take,
                        'label': inv.move_id.name,
                    })

                    discount_amount = inv.discount or 0.0

                    if (
                        discount_amount
                        and not float_is_zero(discount_amount, precision_digits=precision)
                        and float_compare(
                            inv.amount_to_apply,
                            inv.debit - discount_amount,
                            precision_digits=precision
                        ) == 0
                    ):
                        discount_journal = self.env['account.journal'].browse(1964)

                        if not discount_journal.exists():
                            raise UserError(
                                'No existe el diario de descuento financiero con ID 1964.'
                            )

                        payable_line = inv.move_id.line_ids.filtered(
                            lambda l: (
                                l.account_id.account_type == 'liability_payable'
                                and not l.reconciled
                            )
                        )[:1]

                        if not payable_line:
                            raise UserError(
                                f'No se encontró cuenta por pagar abierta en {inv.move_id.name}.'
                            )

                        credit_note = self.env['account.move'].create({
                            'move_type': 'in_refund',
                            'partner_id': partner_id,
                            'invoice_date': cruce_date,
                            'date': cruce_date,
                            'journal_id': discount_journal.id,
                            'ref': f'Descuento {inv.move_id.name}',
                            'invoice_line_ids': [(0, 0, {
                                'name': 'Descuento financiero',
                                'quantity': 1,
                                'price_unit': discount_amount,
                                'account_id': payable_line.account_id.id,
                            })],
                        })

                        credit_note.action_post()

                        cn_line = credit_note.line_ids.filtered(
                            lambda l: (
                                l.account_id.account_type == 'liability_payable'
                                and not l.reconciled
                            )
                        )[:1]

                        if payable_line and cn_line:
                            (payable_line + cn_line).reconcile()

                if not float_is_zero(needed, precision_digits=precision):
                    raise UserError(
                        f'No hay suficiente saldo de facturas para cubrir el cruce por {total_credits}.'
                    )

                for l in payment_nc_lines:
                    if l.document_type == 'payment':
                        move = l.payment_id.move_id
                        label = l.payment_id.name or move.name

                        normalized_lines.append({
                            'document_type': 'payment',
                            'move': move,
                            'move_id': False,
                            'payment_id': l.payment_id.id,
                            'amount': l.amount_to_apply,
                            'label': label,
                        })

                    else:
                        move = l.move_id
                        label = move.name

                        normalized_lines.append({
                            'document_type': 'credit_note',
                            'move': move,
                            'move_id': move.id,
                            'payment_id': False,
                            'amount': l.amount_to_apply,
                            'label': label,
                        })

                _process_single_cruce(
                    cruce_date,
                    normalized_lines
                )

        self.search([]).unlink()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }