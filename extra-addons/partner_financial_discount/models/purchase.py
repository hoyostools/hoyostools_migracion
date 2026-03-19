# -*- coding: utf-8 -*-
# © <2022> <AteneoLab>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from datetime import timedelta

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    financial_discount_percentage = fields.Float(
        string='% Descuento Financiero',
        store=True
    )
    maximum_date_financial_discount = fields.Integer(string="Días Máximo para Descuento Financiero", store=True)
    financial_discount_deadline = fields.Date(
        string="Fecha Límite Descuento Financiero",
        compute="_compute_deadline_date_financial_discount",
        store=True
    )

    @api.onchange('partner_id')
    def get_financial_discount(self):
        for order in self:
            order.financial_discount_percentage = order.partner_id.financial_discount_percentage
            order.maximum_date_financial_discount = order.partner_id.maximum_date_financial_discount

    @api.depends('date_order', 'maximum_date_financial_discount')
    def _compute_deadline_date_financial_discount(self):
        for order in self:
            if order.date_order and order.maximum_date_financial_discount:
                order.financial_discount_deadline = order.date_order + timedelta(days=order.maximum_date_financial_discount)
            else:
                order.financial_discount_deadline = False


