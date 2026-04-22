# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CreditConfigWizard(models.TransientModel):
    _name = "credit.config.wizard"
    _description = "Configuración de Crédito"

    partner_id = fields.Many2one("res.partner", string="Cliente", required=True)

    credit_only_invoiced = fields.Boolean(string="Solo Facturado")
    credit_only_sales = fields.Boolean(string="Solo Ventas")

    receivable_amount = fields.Float(string="Por Cobrar", readonly=True)
    pending_reconcile_amount = fields.Float(string="Pendiente por Cruzar", readonly=True)

    over_quota_percent_enabled = fields.Boolean(string="Sobre Cupo %")
    over_quota_percent = fields.Float(string="Porcentaje Sobre Cupo %")
    over_quota_percent_value = fields.Float(string="Valor Sobre Cupo %", readonly=True)

    over_quota_manual_enabled = fields.Boolean(string="Sobre Cupo Manual")
    over_quota_manual_value = fields.Float(string="Valor Sobre Cupo Manual")

    blocking_overdue_enabled = fields.Boolean(string="Bloqueo Días Mora")
    blocking_overdue_days = fields.Float(string="Días para Bloqueo por Mora")

    sale_order_open_amount = fields.Float(string="Valor Órdenes de Venta Sin Factura", readonly=True)
    available_credit = fields.Float(string="Cupo Disponible", readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        partner = self.env["res.partner"].browse(self.env.context.get("default_partner_id"))
        if partner:
            res.update({
                "partner_id": partner.id,
                "credit_only_invoiced": partner.credit_only_invoiced,
                "credit_only_sales": partner.credit_only_sales,
                "receivable_amount": partner.receivable_amount,
                "pending_reconcile_amount": partner.pending_reconcile_amount,
                "over_quota_percent_enabled": partner.over_quota_percent_enabled,
                "over_quota_percent": partner.over_quota_percent,
                "over_quota_percent_value": partner.over_quota_percent_value,
                "over_quota_manual_enabled": partner.over_quota_manual_enabled,
                "over_quota_manual_value": partner.over_quota_manual_value,
                "blocking_overdue_enabled": partner.blocking_overdue_enabled,
                "blocking_overdue_days": partner.blocking_overdue_days,
                "sale_order_open_amount": partner.sale_order_open_amount,
                "available_credit": partner.available_credit,
            })
        return res

    @api.onchange("over_quota_percent_enabled", "over_quota_percent", "partner_id")
    def _onchange_percent_values(self):
        for wizard in self:
            wizard.over_quota_percent_value = 0.0
            if wizard.over_quota_percent_enabled and wizard.partner_id:
                wizard.over_quota_percent_value = wizard.partner_id.credit_limit * (wizard.over_quota_percent / 100.0)

    def action_save(self):
        self.ensure_one()
        partner = self.partner_id.commercial_partner_id
        partner.write({
            "credit_only_invoiced": self.credit_only_invoiced,
            "credit_only_sales": self.credit_only_sales,
            "over_quota_percent_enabled": self.over_quota_percent_enabled,
            "over_quota_percent": self.over_quota_percent,
            "over_quota_manual_enabled": self.over_quota_manual_enabled,
            "over_quota_manual_value": self.over_quota_manual_value,
            "blocking_overdue_enabled": self.blocking_overdue_enabled,
            "blocking_overdue_days": self.blocking_overdue_days,
        })
        return {"type": "ir.actions.act_window_close"}