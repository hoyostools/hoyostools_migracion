# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    is_credit_main_contact = fields.Boolean(string="Es contacto principal crédito", compute="_compute_is_credit_main_contact")

    # ---------------------------------------------------------
    # Tab Gestión Crédito
    # ---------------------------------------------------------
    control_credit = fields.Boolean(string="Controlar Crédito", tracking=True)
    credit_limit = fields.Float(string="Límite de Crédito", tracking=True)
    credit_limit_with_conditions = fields.Float(string="Límite Crédito con Condiciones", compute="_compute_credit_limit_with_conditions", store=True)

    risk_category_id = fields.Many2one("credit.risk.type", string="Categoría de Riesgo", domain=[("active", "=", True)],)
    

    # ---------------------------------------------------------
    # Configuración crédito por contacto principal
    # ---------------------------------------------------------
    credit_only_invoiced = fields.Boolean(string="Solo Facturado")
    credit_only_sales = fields.Boolean(string="Solo Ventas")

    receivable_amount = fields.Float(
        string="Por Cobrar",
        compute="_compute_credit_metrics",
        store=False,
    )
    pending_reconcile_amount = fields.Float(
        string="Pendiente por Cruzar",
        compute="_compute_credit_metrics",
        store=False,
    )

    over_quota_percent_enabled = fields.Boolean(string="Sobre Cupo %", tracking=True)
    over_quota_percent = fields.Float(string="Porcentaje Sobre Cupo %", tracking=True)

    over_quota_percent_value = fields.Float(
        string="Valor Sobre Cupo %",
        compute="_compute_over_quota_values",
        store=True,
    )

    over_quota_manual_enabled = fields.Boolean(string="Sobre Cupo Manual", tracking=True)
    over_quota_manual_value = fields.Float(string="Valor Sobre Cupo Manual", tracking=True)

    blocking_overdue_enabled = fields.Boolean(string="Bloqueo Días Mora", tracking=True)
    blocking_overdue_days = fields.Float(string="Días para Bloqueo por Mora", tracking=True)

    sale_order_open_amount = fields.Float(
        string="Valor Órdenes de Venta Sin Factura",
        compute="_compute_credit_metrics",
        store=False,
    )

    available_credit = fields.Float(
        string="Cupo Disponible",
        compute="_compute_credit_metrics",
        store=False,
    )
    
    days_overdue = fields.Integer(
        string="Días Mora",
        compute="_compute_days_overdue",
        store=False,
    )

    credit_blocked = fields.Boolean(
        string="Bloqueo",
        compute="_compute_credit_blocked",
        store=True,
        tracking=True,
        readonly=False,
    )
    
    # ---------------------------------------------------------
    # Computes
    # ---------------------------------------------------------
    @api.depends("commercial_partner_id")
    def _compute_is_credit_main_contact(self):
        for partner in self:
            partner.is_credit_main_contact = partner.id == partner.commercial_partner_id.id

    @api.depends(
        "credit_limit",
        "over_quota_percent_enabled",
        "over_quota_percent_value",
        "over_quota_manual_enabled",
        "over_quota_manual_value",
    )
    def _compute_credit_limit_with_conditions(self):
        for partner in self:
            extra = 0.0
            if partner.over_quota_percent_enabled:
                extra = partner.over_quota_percent_value
            elif partner.over_quota_manual_enabled:
                extra = partner.over_quota_manual_value
            partner.credit_limit_with_conditions = partner.credit_limit + extra

    @api.depends("credit_limit", "over_quota_percent_enabled", "over_quota_percent")
    def _compute_over_quota_values(self):
        for partner in self:
            partner.over_quota_percent_value = 0.0
            if partner.over_quota_percent_enabled and partner.over_quota_percent:
                partner.over_quota_percent_value = partner.credit_limit * (partner.over_quota_percent / 100.0)

    @api.depends(
        "credit_limit_with_conditions",
        "credit_only_invoiced",
        "credit_only_sales",
        "commercial_partner_id",
    )
    def _compute_credit_metrics(self):

        for partner in self:

            commercial = partner.commercial_partner_id

            if not commercial or not commercial.id:
                partner.receivable_amount = 0.0
                partner.pending_reconcile_amount = 0.0
                partner.sale_order_open_amount = 0.0
                partner.available_credit = partner.credit_limit_with_conditions
                continue

            commercial_partners = self.env["res.partner"].search([
                ("id", "child_of", commercial.id)
            ])

            invoices = self.env["account.move"].search([
                ("partner_id", "in", commercial_partners.ids),
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "in", ["not_paid", "partial", "in_payment"]),
            ])

            receivable_amount = sum(invoices.mapped("amount_residual"))

            credit_notes = self.env["account.move"].search([
                ("partner_id", "in", commercial_partners.ids),
                ("move_type", "=", "out_refund"),
                ("state", "=", "posted"),
                ("payment_state", "in", ["not_paid", "partial", "in_payment"]),
            ])

            credit_note_available = sum(credit_notes.mapped("amount_residual"))

            payment_lines = self.env["account.move.line"].search([
                ("partner_id", "in", commercial_partners.ids),
                ("parent_state", "=", "posted"),
                ("account_id.account_type", "=", "asset_receivable"),
                ("reconciled", "=", False),
                ("payment_id", "!=", False),
            ])

            payment_available = sum(abs(line.amount_residual) for line in payment_lines)

            pending_reconcile = credit_note_available + payment_available

            sale_orders = self.env["sale.order"].search([
                ("partner_id", "in", commercial_partners.ids),
                ("state", "=", "sale"),
                ("invoice_status", "!=", "invoiced"),
            ])

            sale_open_amount = sum(sale_orders.mapped("amount_total"))

            available_credit = (
                commercial.credit_limit_with_conditions
                - receivable_amount
                + pending_reconcile
                - sale_open_amount
            )

            partner.receivable_amount = receivable_amount
            partner.pending_reconcile_amount = pending_reconcile
            partner.sale_order_open_amount = sale_open_amount
            partner.available_credit = available_credit
            
    def _compute_days_overdue(self):

        for partner in self:

            partner.days_overdue = 0

            if not partner.control_credit:
                continue

            partner.days_overdue = partner._get_credit_overdue_days()
            
    def _compute_credit_blocked(self):

        for partner in self:

            blocked = False

            # Si no controla crédito
            if not partner.control_credit:
                partner.credit_blocked = False
                continue

            # ============================================
            # BLOQUEO POR CUPO
            # ============================================

            if partner.available_credit < 0:
                blocked = True

            # ============================================
            # BLOQUEO POR MORA
            # ============================================

            overdue_days = partner._get_credit_overdue_days()

            if overdue_days > 0:
                blocked = True

            partner.credit_blocked = blocked

    # ---------------------------------------------------------
    # Constraints
    # ---------------------------------------------------------
    @api.constrains("credit_only_invoiced", "credit_only_sales")
    def _check_credit_control_mode(self):
        for partner in self:
            if partner.credit_only_invoiced and partner.credit_only_sales:
                raise ValidationError(_("Solo puede activar una opción de control: Solo Facturado o Solo Ventas."))

    @api.constrains("over_quota_percent_enabled", "over_quota_manual_enabled")
    def _check_over_quota_mode(self):
        for partner in self:
            if partner.over_quota_percent_enabled and partner.over_quota_manual_enabled:
                raise ValidationError(_("Solo puede activar un tipo de sobrecupo: porcentaje o manual."))

    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------
    def action_open_credit_config(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Configurar Crédito"),
            "res_model": "credit.config.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.commercial_partner_id.id,
            },
        }

    # ---------------------------------------------------------
    # Credit helper methods
    # ---------------------------------------------------------
    def _get_credit_overdue_days(self):
        self.ensure_one()
        commercial = self.commercial_partner_id
        commercial_partners = self.env["res.partner"].search([
            ("id", "child_of", commercial.id)
        ])
        today = fields.Date.context_today(self)

        overdue_invoices = self.env["account.move"].search([
            ("partner_id", "in", commercial_partners.ids),
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            ("payment_state", "in", ["not_paid", "partial", "in_payment"]),
            ("invoice_date_due", "!=", False),
            ("invoice_date_due", "<", today),
        ])

        max_days = 0
        for inv in overdue_invoices:
            days = (today - inv.invoice_date_due).days
            if days > max_days:
                max_days = days
        return max_days