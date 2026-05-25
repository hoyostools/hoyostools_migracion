import logging
import time
import uuid
from datetime import date, timedelta

from odoo import _, models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


_logger = logging.getLogger(__name__)


class SemiAutoReconciliationLine(models.TransientModel):
    _name = 'semi.auto.reconciliation.line'
    _description = 'Línea de conciliación semiautomática'

    # ==============
    # CAMPOS DEL MODELO
    # ==============

    partner_id = fields.Many2one('res.partner', string='Cliente')
    invoice_date = fields.Date(related='move_id.invoice_date', string='Fecha Factura', store=True)
    move_id = fields.Many2one('account.move', string='Factura / Nota crédito')
    invoice_payment_term_id = fields.Many2one(
        'account.payment.term',
        related='move_id.invoice_payment_term_id',
        string='Término de Pago',
        store=True
    )
    date = fields.Date(related='payment_id.date', string='Fecha Pago', store=True)
    payment_id = fields.Many2one('account.payment', string='Pago')
    due_date = fields.Date(string="Fecha Vencimiento", compute='_compute_due_date', store=True)
    is_due = fields.Boolean(compute='_compute_due_status', store=False)
    is_warning_due = fields.Boolean(compute='_compute_due_status', store=False)

    document_type = fields.Selection([
        ('invoice', 'Factura'),
        ('credit_note', 'Nota de Crédito'),
        ('payment', 'Pago'),
    ], string='Tipo', required=True)

    reconcile_full = fields.Boolean(string="Conciliar Todo")
    debit = fields.Monetary(string='Débito')
    credit = fields.Monetary(string='Crédito')
    amount_to_apply = fields.Monetary(
        string='Aplicar',
        compute='_compute_amount_to_apply',
        inverse='_inverse_amount_to_apply',
        store=True,
        default=0.0
    )
    currency_id = fields.Many2one('res.currency', string='Moneda')
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, readonly=True)
    discount = fields.Monetary(string='Descuento financiero', compute='_compute_discount')

    def _compute_discount(self):
        for record in self:
            record.discount = 0.0
            if record.due_date:
                if record.due_date > date.today():
                    record.discount = record.move_id.amount_untaxed * (record.invoice_payment_term_id.discount_percentage / 100)

    # ==============================
    # CÁLCULO DE ESTADO DE VENCIMIENTO
    # ==============================

    @api.depends('due_date')
    def _compute_due_status(self):
        today = date.today()
        warning_limit = today + timedelta(days=5)
        for rec in self:
            rec.is_due = rec.due_date and rec.due_date <= today
            rec.is_warning_due = rec.due_date and today < rec.due_date <= warning_limit

    @api.depends('move_id')
    def _compute_due_date(self):
        for rec in self:
            rec.due_date = rec.move_id.invoice_date_due if rec.move_id else False

    # ===================
    # VALIDACIONES DE MONTO
    # ===================

    @api.constrains('amount_to_apply')
    def _check_amount_to_apply_sign(self):
        precision = self.env['decimal.precision'].precision_get('Account')
        for rec in self:
            if rec.document_type == 'invoice' and float_compare(rec.amount_to_apply, 0.0, precision_digits=precision) < 0:
                raise ValidationError("❌ Para facturas, el monto a aplicar debe ser positivo.")
            if rec.document_type in ['credit_note', 'payment'] and float_compare(rec.amount_to_apply, 0.0, precision_digits=precision) > 0:
                raise ValidationError("❌ Para pagos o notas de crédito, el monto a aplicar debe ser negativo.")

    @api.onchange('amount_to_apply')
    def _onchange_amount_to_apply(self):
        precision = self.env['decimal.precision'].precision_get('Account')
        if self.debit and float_compare(self.amount_to_apply, (self.debit - self.discount),
                                        precision_digits=precision) > 0:
            self.amount_to_apply = self.debit - self.discount
        elif self.credit and float_compare(self.amount_to_apply, self.credit, precision_digits=precision) > 0:
            self.amount_to_apply = self.credit

    @api.depends('reconcile_full', 'debit', 'credit', 'document_type')
    def _compute_amount_to_apply(self):
        for rec in self:
            if rec.reconcile_full:
                if rec.document_type in ['invoice']:
                    rec.amount_to_apply = rec.debit - rec.discount
                elif rec.document_type in ['credit_note', 'payment']:
                    rec.amount_to_apply = -rec.credit
                else:
                    rec.amount_to_apply = 0.0

    @api.depends('amount_to_apply')
    def _inverse_amount_to_apply(self):
        # No hace nada, pero permite editar cuando el switch está desactivado
        pass

    # ============================
    # CARGAR DOCUMENTOS EN TRANSIENT
    # ============================

    @api.model
    def load_documents_for_partners(self, partners):
        all_partner_ids = partners.ids + self.env['res.partner'].search([('parent_id', 'in', partners.ids)]).ids

        # Incluir subcontactos (child_ids) y el mismo partner
        for partner in partners:
            all_partner_ids += [partner.id] + partner.child_ids.ids

        invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
            ('amount_residual', '>', 0),
            ('partner_id', 'in', all_partner_ids),
        ])
        credit_notes = self.env['account.move'].search([
            ('move_type', '=', 'out_refund'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
            ('amount_residual', '>', 0),
            ('partner_id', 'in', all_partner_ids),
        ])
        payments = self.env['account.payment'].search([
            ('state', '=', 'posted'),
            ('partner_id', 'in', all_partner_ids),
        ])

        for partner in partners:
            # Todos los documentos asociados a este partner o sus hijos
            related_ids = [partner.id] + partner.child_ids.ids
            lines = []

            for inv in invoices.filtered(lambda i: i.partner_id.id in related_ids):
                lines.append((0, 0, {
                    'partner_id': partner.id,  # Asociar al contacto principal
                    'move_id': inv.id,
                    'document_type': 'invoice',
                    'debit': inv.amount_residual,
                    'credit': 0.0,
                    'amount_to_apply': 0.0,
                    'currency_id': inv.currency_id.id,
                }))

            for cr in credit_notes.filtered(lambda c: c.partner_id.id in related_ids):
                lines.append((0, 0, {
                    'partner_id': partner.id,
                    'move_id': cr.id,
                    'document_type': 'credit_note',
                    'debit': 0.0,
                    'credit': cr.amount_residual,
                    'amount_to_apply': 0.0,
                    'currency_id': cr.currency_id.id,
                }))

            for pay in payments.filtered(lambda p: p.partner_id.id in related_ids):
                receivable_line = pay.move_id.line_ids.filtered(
                    lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
                )
                if receivable_line:
                    lines.append((0, 0, {
                        'partner_id': partner.id,
                        'payment_id': pay.id,
                        'document_type': 'payment',
                        'debit': 0.0,
                        'credit': abs(receivable_line[0].amount_residual),
                        'amount_to_apply': 0.0,
                        'currency_id': pay.currency_id.id,
                    }))

            if any(l[2]['debit'] > 0 for l in lines) and any(l[2]['credit'] > 0 for l in lines):
                self.create([l[2] for l in lines])

    # ============================
    # ACCIÓN DE CONCILIACIÓN
    # ============================

    @api.model
    def action_reconcile_selected(self, ids):

        # ---------------------------------------------------------------------
        # 1) Cargar líneas seleccionadas
        # ---------------------------------------------------------------------
        lines = self.browse(ids)
        if not lines:
            raise UserError("No se seleccionaron líneas.")

        precision = self.env['decimal.precision'].precision_get('Account')
        _logger.info("Inicio de conciliación con líneas: %s", ids)

        # ---------------------------------------------------------------------
        # 2) Validar y agrupar por partner
        # ---------------------------------------------------------------------
        grouped_by_partner = {}
        for line in lines:
            # Validación: no permitir 0
            if float_is_zero(line.amount_to_apply, precision_digits=precision):
                raise UserError(
                    f"El monto a aplicar para el documento '{line.move_id.name or line.payment_id.name}' no puede ser cero."
                )

            # Validación de signo
            if line.document_type == 'invoice' and line.amount_to_apply < 0:
                raise UserError(
                    f"Para facturas, el monto a aplicar debe ser positivo. Documento: {line.move_id.name}"
                )
            if line.document_type in ['payment', 'credit_note'] and line.amount_to_apply > 0:
                raise UserError(
                    f"Para pagos/notas crédito, el monto a aplicar debe ser negativo. "
                    f"Documento: {line.payment_id.name if line.document_type == 'payment' else line.move_id.name}"
                )

            grouped_by_partner.setdefault(line.partner_id.id, []).append(line)

        # ---------------------------------------------------------------------
        # Helper: obtener la línea receivable “real” del documento (factura/pago/NC)
        # ---------------------------------------------------------------------
        def _get_open_receivable_line_from_move(move):
            aml = move.line_ids.filtered(
                lambda l: l.account_id.account_type == "asset_receivable"
                and not float_is_zero(l.amount_residual, precision_digits=precision)
            )
            return aml[:1]  # recordset de 0 o 1

        # ---------------------------------------------------------------------
        # Helper: obtener fecha “clave” de Recaudos/NC
        #  - Pago: payment.date
        #  - Nota crédito: move.date o invoice_date (prioridad: date contable)
        # ---------------------------------------------------------------------
        def _get_recaudo_nc_date(wl):
            if wl.document_type == "payment":
                d = wl.payment_id.date
                _logger.info("Fecha agrupación (PAGO) %s -> %s", wl.payment_id.name, d)
                return d
            if wl.document_type == "credit_note":
                d = wl.move_id.date or wl.move_id.invoice_date
                _logger.info(
                    "Fecha agrupación (NC) %s -> %s (move.date=%s, invoice_date=%s)",
                    wl.move_id.name, d, wl.move_id.date, wl.move_id.invoice_date
                )
                return d
            return False

        # ---------------------------------------------------------------------
        # 3) Configuración: diario de cruce como PAGO + cuenta "liquidez" (sin conciliar)
        # ---------------------------------------------------------------------
        payment_journal = self.env['account.journal'].search([
            ('code', '=', 'PAYC')
        ], limit=1)

        bridge_journal = self.env['account.journal'].search([
            ('code', '=', 'BRDG')
        ], limit=1)

        if not payment_journal:
            raise UserError("No existe el diario PAYC.")

        if not bridge_journal:
            raise UserError("No existe el diario BRDG.")
        # if not journal:
        #     raise UserError("No existe un diario llamado 'Cruce Clientes'.")

        # Para crear account.payment el diario debe ser bank/cash
        if payment_journal.type not in ('bank', 'cash'):
            raise UserError("El diario 'Cruce Clientes' debe ser tipo Banco o Caja para poder crear Pagos (account.payment).")

        clearing_account = payment_journal.default_account_id
        if not clearing_account:
            raise UserError("El diario 'Cruce Clientes' debe tener una cuenta por defecto (default_account_id).")

        # NOTA: aquí YA NO exigimos 'Allow Reconciliation' porque en cuentas Liquidity
        # muchas bases lo bloquean. El saldo quedará neto en 0, aunque las líneas
        # de liquidez queden sin conciliar.

        payment_method_line = payment_journal.inbound_payment_method_line_ids[:1]
        if not payment_method_line:
            raise UserError("El diario 'Cruce Clientes' no tiene método de pago de entrada configurado (inbound).")

        # ---------------------------------------------------------------------
        # 4) Procesar partner por partner, creando 1 cruce por cada fecha distinta
        # ---------------------------------------------------------------------
        for partner_id, partner_lines in grouped_by_partner.items():
            _logger.info("Procesando partner: %s", partner_id)

            invoice_lines = [l for l in partner_lines if l.document_type == "invoice"]
            recaudo_nc_lines = [l for l in partner_lines if l.document_type in ("payment", "credit_note")]

            if not recaudo_nc_lines:
                raise UserError("Debe seleccionar al menos un recaudo o nota crédito para generar cruces por fecha.")

            # Validación total general: sum(invoice) == sum(abs(recaudos/NC))
            total_invoices = sum(l.amount_to_apply for l in invoice_lines)
            total_credits = sum(abs(l.amount_to_apply) for l in recaudo_nc_lines)
            if float_compare(total_invoices, total_credits, precision_digits=precision) != 0:
                raise UserError(
                    f"⚠️ El total a aplicar en facturas ({total_invoices}) no coincide con el total de recaudos/NC ({total_credits})."
                )

            # # Agrupar recaudos/NC por fecha
            # groups_by_date = {}
            # for l in recaudo_nc_lines:
            #     d = _get_recaudo_nc_date(l)
            #     if not d:
            #         raise UserError(
            #             f"No se pudo determinar la fecha para el documento "
            #             f"{l.payment_id.name if l.document_type == 'payment' else l.move_id.name}."
            #         )
            #     groups_by_date.setdefault(d, []).append(l)

            # # Ordenar fechas ascendente (aplica primero lo más antiguo)
            # sorted_dates = sorted(groups_by_date.keys())
            
            normalized_lines = []

            # Preparar cola de facturas a consumir
            invoice_queue = sorted(
                invoice_lines,
                key=lambda x: (
                    x.move_id.invoice_date_due or x.move_id.invoice_date or x.move_id.date or fields.Date.today(),
                    x.move_id.name or "",
                    x.id
                )
            )
            invoice_remaining = {l.id: l.amount_to_apply for l in invoice_queue}

            # -----------------------------------------------------------------
            # Helper interno: ejecuta un cruce como PAGO visible en Clientes > Pagos
            #  - Crea account.payment (Cruce)
            #  - Crea asiento puente (bridge_move) para absorber pagos/NC originales
            #  - Concilia:
            #       Facturas ↔ Payment(Cruce) en CxC
            #       Pagos/NC ↔ BridgeMove en CxC
            #  - NO concilia liquidez (clearing) porque cuentas bank/cash suelen
            #    no permitir reconcile. El neto queda en 0.
            # -----------------------------------------------------------------
            def _process_single_cruce(cruce_date, normalized_lines):
                debit_total = 0.0
                credit_total = 0.0
                for item in normalized_lines:
                    amt = item["amount"]
                    if amt > 0:
                        debit_total += amt
                    else:
                        credit_total += abs(amt)

                if float_compare(debit_total, credit_total, precision_digits=precision) != 0:
                    raise UserError(
                        f"⚠️ El total del débito ({debit_total}) y crédito ({credit_total}) no coincide para la fecha {cruce_date}."
                    )

                cruce_name = self.env['ir.sequence'].next_by_code('cruce.saldos') or f"CRUCE/{uuid.uuid4().hex[:6].upper()}"

                # 1) Crear PAGO (account.payment) = "Cruce"
                payment_vals = {
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "partner_id": partner_id,
                    "amount": debit_total,
                    "date": fields.Datetime.now().date(),
                    "journal_id": payment_journal.id,
                    "payment_method_line_id": payment_method_line.id,
                    "ref": f"Cruce {cruce_name}",
                }
                cruce_payment = self.env["account.payment"].create(payment_vals)
                cruce_payment.action_post()
                _logger.info("✅ Pago de cruce creado y posteado: %s | Fecha: %s", cruce_payment.name, cruce_date)

                pay_move = cruce_payment.move_id

                # Línea CxC del pago (normalmente CREDIT en receivable)
                pay_recv_lines = pay_move.line_ids.filtered(
                    lambda l: l.account_id.account_type == "asset_receivable" and not l.reconciled
                )
                if not pay_recv_lines:
                    raise UserError("No se encontró línea por cobrar (receivable) en el pago de cruce.")
                pay_recv_line = pay_recv_lines[0]

                # 2) Crear ASIENTO PUENTE (bridge_move) para absorber pagos/NC originales
                bridge_line_vals = []
                total_bridge_recv = 0.0

                for item in normalized_lines:
                    if item["document_type"] == "invoice":
                        continue

                    move = item["move"]
                    orig_line = _get_open_receivable_line_from_move(move)
                    if not orig_line:
                        raise UserError(f"No se encontró línea receivable abierta en {move.name}")
                    orig_line = orig_line[0]

                    amount = abs(item["amount"])
                    if float_is_zero(amount, precision_digits=precision):
                        continue

                    total_bridge_recv += amount

                    # Débito a CxC (misma cuenta del documento original)
                    bridge_line_vals.append((0, 0, {
                        "name": item["label"],
                        "partner_id": partner_id,
                        "account_id": orig_line.account_id.id,
                        "debit": amount,
                        "credit": 0.0,
                    }))

                # Contrapartida: crédito a la cuenta de "liquidez" del diario (default_account_id)
                bridge_line_vals.append((0, 0, {
                    "name": f"Contrapartida liquidez {cruce_name}",
                    "partner_id": partner_id,
                    "account_id": clearing_account.id,
                    "debit": 0.0,
                    "credit": total_bridge_recv,
                }))

                bridge_move = self.env["account.move"].create({
                    "ref": f"Bridge {cruce_name}",
                    "journal_id": bridge_journal.id,
                    "move_type": "entry",
                    "partner_id": partner_id,
                    "date": cruce_date,
                    "line_ids": bridge_line_vals,
                })
                bridge_move.action_post()
                _logger.info("✅ Asiento puente creado y posteado: %s | Fecha: %s", bridge_move.name, cruce_date)

                bridge_recv_lines = bridge_move.line_ids.filtered(
                    lambda l: l.account_id.account_type == "asset_receivable" and not l.reconciled
                )

                # 3) Crear documento cruce.saldos (soporte) apuntando al move del PAGO
                cruce = self.env["cruce.saldos"].create({
                    "name": cruce_name,
                    "partner_id": partner_id,
                    "date": fields.Datetime.now().date(),
                    "total_amount": debit_total,
                    "move_id": pay_move.id,  # principal = move del pago
                })
                cruce._sync_move_lines_from_move()

                for item in normalized_lines:
                    cruce.line_ids.create({
                        "cruce_id": cruce.id,
                        "move_id": item.get("move_id") or False,
                        "payment_id": item.get("payment_id") or False,
                        "document_type": item["document_type"],
                        "amount_applied": item["amount"],
                    })

                # 4) Conciliar FACTURAS vs PAGO CRUCE (receivable)
                for item in normalized_lines:
                    if item["document_type"] != "invoice":
                        continue

                    move = item["move"]
                    inv_line = _get_open_receivable_line_from_move(move)
                    if not inv_line:
                        _logger.info("Factura %s sin residual receivable (posible ya conciliada).", move.name)
                        continue
                    inv_line = inv_line[0]

                    amount = abs(item["amount"])
                    if float_is_zero(amount, precision_digits=precision):
                        continue

                    self.env["account.partial.reconcile"].create({
                        "debit_move_id": inv_line.id,
                        "credit_move_id": pay_recv_line.id,
                        "amount": amount,
                        "debit_amount_currency": amount,
                        "credit_amount_currency": amount,
                    })
                    _logger.info("✅ Conciliado: FACTURA %s ↔ PAGO CRUCE %s por %s", move.name, cruce_payment.name, amount)

                # 5) Conciliar PAGOS/NC ORIGINALES vs ASIENTO PUENTE (receivable)
                for item in normalized_lines:
                    if item["document_type"] == "invoice":
                        continue

                    move = item["move"]
                    orig_line = _get_open_receivable_line_from_move(move)
                    if not orig_line:
                        _logger.info("Documento %s sin residual receivable (posible ya conciliado).", move.name)
                        continue
                    orig_line = orig_line[0]

                    amount = abs(item["amount"])
                    if float_is_zero(amount, precision_digits=precision):
                        continue

                    bridge_match = bridge_recv_lines.filtered(
                        lambda l: l.partner_id.id == partner_id
                        and float_compare(l.debit, amount, precision_digits=precision) == 0
                        and (l.name == item["label"])
                    )
                    if not bridge_match:
                        bridge_match = bridge_recv_lines.filtered(
                            lambda l: l.partner_id.id == partner_id
                            and float_compare(l.debit, amount, precision_digits=precision) == 0
                        )
                    if not bridge_match:
                        raise UserError(
                            f"No se encontró línea DÉBITO en el puente ({bridge_move.name}) "
                            f"para conciliar {move.name} por {amount}."
                        )

                    bridge_line = bridge_match[0]

                    self.env["account.partial.reconcile"].create({
                        "debit_move_id": bridge_line.id,
                        "credit_move_id": orig_line.id,
                        "amount": amount,
                        "debit_amount_currency": amount,
                        "credit_amount_currency": amount,
                    })
                    _logger.info("✅ Conciliado: ORIG %s ↔ PUENTE %s por %s", move.name, bridge_move.name, amount)

                # NOTA: No conciliamos líneas de liquidez/caja/banco (default_account_id)
                # porque típicamente no permiten reconcile. El neto queda en 0.

                _logger.info("✅ Cruce finalizado como PAGO (sin reconciliar liquidez). Fecha: %s | Pago: %s", cruce_date, cruce_payment.name)

            # -----------------------------------------------------------------
            # 5) Por cada fecha: armar conjunto de líneas (facturas parcializadas + recaudos/NC)
            # -----------------------------------------------------------------
            cruce_date = fields.Date.today()

            group_total = sum(abs(l.amount_to_apply) for l in recaudo_nc_lines)

            needed = group_total
            normalized_lines = []

            # =========================================================
            # FACTURAS
            # =========================================================

            for inv in invoice_queue:

                if float_is_zero(needed, precision_digits=precision):
                    break

                rem = invoice_remaining.get(inv.id, 0.0)

                if float_is_zero(rem, precision_digits=precision):
                    continue

                take = rem if float_compare(
                    rem,
                    needed,
                    precision_digits=precision
                ) <= 0 else needed

                invoice_remaining[inv.id] = rem - take
                needed -= take

                normalized_lines.append({
                    "document_type": "invoice",
                    "move": inv.move_id,
                    "move_id": inv.move_id.id,
                    "payment_id": False,
                    "amount": take,
                    "label": inv.move_id.name,
                })

                # ==========================================
                # DESCUENTO
                # ==========================================

                discount_pct = getattr(inv, "discount", 0.0)

                if discount_pct:

                    if (
                        not float_is_zero(discount_pct, precision_digits=precision)
                        and inv.amount_to_apply == (inv.debit - discount_pct)
                    ):

                        credit_note = self.env['account.move'].create({
                            'move_type': 'out_refund',
                            'partner_id': partner_id,
                            'invoice_date': cruce_date,
                            'journal_id': 1854,
                            'date': cruce_date,
                            'ref': f"Descuento {inv.move_id.name}",
                            'invoice_line_ids': [(0, 0, {
                                'name': 'Descuento aplicado',
                                'quantity': 1,
                                'price_unit': discount_pct,
                                'account_id': inv.move_id.line_ids[0].account_id.id,
                            })]
                        })

                        credit_note.action_post()

                        inv_line = inv.move_id.line_ids.filtered(
                            lambda l: (
                                l.account_id.account_type == "asset_receivable"
                                and not l.reconciled
                            )
                        )[:1]

                        cn_line = credit_note.line_ids.filtered(
                            lambda l: (
                                l.account_id.account_type == "asset_receivable"
                                and not l.reconciled
                            )
                        )[:1]

                        if inv_line and cn_line:
                            (inv_line + cn_line).reconcile()

            # =========================================================
            # VALIDACIÓN
            # =========================================================

            if not float_is_zero(needed, precision_digits=precision):

                raise UserError(
                    f"No hay suficiente saldo de facturas seleccionadas "
                    f"para cubrir el total del cruce por {group_total}."
                )

            # =========================================================
            # PAGOS Y NOTAS CRÉDITO
            # =========================================================

            for l in recaudo_nc_lines:

                if l.document_type == "payment":

                    move = l.payment_id.move_id
                    label = l.payment_id.name or move.name

                    normalized_lines.append({
                        "document_type": "payment",
                        "move": move,
                        "move_id": False,
                        "payment_id": l.payment_id.id,
                        "amount": l.amount_to_apply,
                        "label": label,
                    })

                else:

                    move = l.move_id
                    label = move.name

                    normalized_lines.append({
                        "document_type": "credit_note",
                        "move": move,
                        "move_id": move.id,
                        "payment_id": False,
                        "amount": l.amount_to_apply,
                        "label": label,
                    })

            # =========================================================
            # EJECUTAR UN SOLO CRUCE
            # =========================================================

            _process_single_cruce(cruce_date, normalized_lines)

        # ---------------------------------------------------------------------
        # 6) Limpiar transient (wizard) y recargar vista
        # ---------------------------------------------------------------------
        self.search([]).unlink()
        _logger.info("Fin de la conciliación")
        return {"type": "ir.actions.client", "tag": "reload"}

    def _create_discount_credit_note(self, invoice, partner_id, discount_amount, date):
        if float_is_zero(discount_amount):
            return None

        credit_note = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': partner_id,
            'invoice_date': date,
            'date': date,
            'ref': f"Descuento factura {invoice.name}",
            'invoice_line_ids': [(0, 0, {
                'name': 'Descuento aplicado',
                'quantity': 1,
                'price_unit': discount_amount,
                'account_id': invoice.line_ids[0].account_id.id,
            })]
        })

        credit_note.action_post()
        return credit_note

