# -*- coding: utf-8 -*-
from odoo import _, fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    credit_blocked_limit = fields.Boolean(string="Bloqueo por Cupo", copy=False, readonly=True)
    credit_blocked_overdue = fields.Boolean(string="Bloqueo por Mora", copy=False, readonly=True)

    credit_unlock_overdue = fields.Boolean(string="Desbloqueo por Mora")
    credit_unlock_limit = fields.Boolean(string="Desbloqueo por Cupo")

    credit_limit_assigned = fields.Float(string="Cupo Asignado", readonly=True, copy=False)
    credit_available_at_validation = fields.Float(string="Cupo Disponible Validación", readonly=True, copy=False)
    credit_overdue_days_found = fields.Float(string="Días Mora Detectados", readonly=True, copy=False)
    
    credit_limit = fields.Float(string="Cupo Autorizado", compute="_compute_partner_credit_values", store=True, readonly=True,)
    amount_due = fields.Float(string="Cupo Usado", compute="_compute_partner_credit_values", store=True, readonly=True,)
    
    @api.depends("partner_id")
    def _compute_partner_credit_values(self):

        for order in self:

            order.credit_limit = 0.0
            order.amount_due = 0.0

            if not order.partner_id:
                continue

            partner = order.partner_id.commercial_partner_id

            order.credit_limit = partner.credit_limit
            order.amount_due = partner.receivable_amount

    def _build_credit_block_action(self, message):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Gestión de Crédito"),
                "message": message,
                "type": "danger",
                "sticky": True,
            },
        }

    def _reset_credit_flags(self):
        self.write({
            "credit_blocked_limit": False,
            "credit_blocked_overdue": False,
            "credit_limit_assigned": 0.0,
            "credit_available_at_validation": 0.0,
            "credit_overdue_days_found": 0.0,
        })

    def action_confirm(self):

        for order in self:

            partner = order.partner_id.commercial_partner_id

            # Reset flags antes de validar
            order.write({
                "credit_blocked_limit": False,
                "credit_blocked_overdue": False,
                "credit_limit_assigned": 0.0,
                "credit_available_at_validation": 0.0,
                "credit_overdue_days_found": 0.0,
            })

            if not partner.control_credit:
                continue

            # Solo validar cuando aplica modo SOLO VENTAS
            if not partner.credit_only_sales:
                continue


            available_credit = partner.available_credit
            limit_with_conditions = partner.credit_limit_with_conditions
            max_overdue_days = partner._get_credit_overdue_days()


            blocked_by_limit = (
                available_credit < order.amount_total
                and not order.credit_unlock_limit
            )

            blocked_by_overdue = (
                partner.blocking_overdue_enabled
                and partner.blocking_overdue_days > 0
                and max_overdue_days > partner.blocking_overdue_days
                and not order.credit_unlock_overdue
            )


            # Guardamos SIEMPRE valores informativos
            order.write({
                "credit_limit_assigned": limit_with_conditions,
                "credit_available_at_validation": available_credit,
                "credit_overdue_days_found": max_overdue_days,
                "credit_blocked_limit": blocked_by_limit,
                "credit_blocked_overdue": blocked_by_overdue,
            })


            # Bloqueo por cupo
            if blocked_by_limit:

                msg = _(
                    "Bloqueo por cupo.\n"
                    "Cupo asignado: %(assigned).2f\n"
                    "Cupo disponible: %(available).2f\n"
                    "Total cotización: %(total).2f"
                ) % {
                    "assigned": limit_with_conditions,
                    "available": available_credit,
                    "total": order.amount_total,
                }

                return order._build_credit_block_action(msg)


            # Bloqueo por mora
            if blocked_by_overdue:

                msg = _(
                    "Bloqueo por mora.\n"
                    "Días mora detectados: %(found)s\n"
                    "Días permitidos: %(allowed)s"
                ) % {
                    "found": int(max_overdue_days),
                    "allowed": int(partner.blocking_overdue_days),
                }

                return order._build_credit_block_action(msg)


        # Si no hubo bloqueo → confirmar normalmente
        return super().action_confirm()