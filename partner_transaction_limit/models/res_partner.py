from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class ResPartner(models.Model):
    _inherit = 'res.partner'

    transaction_control_months = fields.Integer(
        string="Control Period (Months)",
        default=12,
        help="Number of months for transaction limit control"
    )
    transaction_control_months_p = fields.Integer(
        string="Control Period (Months)",
        default=12,
        help="Number of months for transaction limit control"
    )
    sales_limit = fields.Float(string="Sales Limit")
    purchase_limit = fields.Float(string="Purchase Limit")
    sales_total_current_period = fields.Float(
        string="Ventas totales en el periodo actual", compute="_compute_sales_total"
    )
    purchase_total_current_period = fields.Float(
        string="Compras totales en el periodo actual", compute="_compute_purchase_total"
    )
    validate_transaction_limits = fields.Boolean(string="Validate Transaction Limits", compute="_compute_validate_transaction_limits")
    validate_transaction_limits_p = fields.Boolean(string="Validate Transaction Limits", compute="_compute_validate_transaction_limits")
    last_update_sale_validation = fields.Date(string="Last Update Sale Validation")
    last_update_purchase_validation = fields.Date(string="Last Update Purchase Validation")

    transaction_validation_document = fields.Binary(string="Transaction Validation Document")
    transaction_validation_document_p = fields.Binary(string="Transaction Validation Document")

    purchase_order_ids = fields.One2many('purchase.order', 'partner_id', string="Purchase Orders")


    def _get_date_range_sale(self):
        current_date = fields.Date.today() if not self.last_update_sale_validation else self.last_update_sale_validation + relativedelta(months=self.transaction_control_months)
        start_date = current_date - relativedelta(months=self.transaction_control_months)
        return start_date, current_date

    def _get_date_range_purchase(self):
        current_date = fields.Date.today() if not self.last_update_purchase_validation else self.last_update_purchase_validation + relativedelta(months=self.transaction_control_months_p)
        start_date = current_date - relativedelta(months=self.transaction_control_months_p)
        return start_date, current_date

    @api.depends('sale_order_ids', 'last_update_sale_validation')
    def _compute_sales_total(self):
        for partner in self:
            partner.update_last_verification_date()
            start_date, end_date = partner._get_date_range_sale()
            partner.sales_total_current_period = sum(
                order.amount_total
                for order in partner.sale_order_ids
                if start_date <= fields.Date.to_date(order.date_order) <= end_date and order.state in ('sale', 'done')
            )

    @api.depends('purchase_line_ids', 'last_update_purchase_validation')
    def _compute_purchase_total(self):
        for partner in self:
            partner.update_last_verification_date()
            start_date, end_date = partner._get_date_range_purchase()
            partner.purchase_total_current_period = sum(
                order.amount_total
                for order in partner.purchase_order_ids
                if start_date <= fields.Date.to_date(order.date_order) <= end_date and order.state in ('purchase', 'done')
            )

    @api.depends('sales_total_current_period', 'purchase_total_current_period')
    def _compute_validate_transaction_limits(self):
        for partner in self:
            partner.validate_transaction_limits = partner.sales_total_current_period <= partner.sales_limit or not partner.sales_limit
            partner.validate_transaction_limits_p = partner.purchase_total_current_period <= partner.purchase_limit or not partner.purchase_limit

    def update_last_verification_date(self):
        for partner in self:
            if partner.last_update_sale_validation:
                if partner.last_update_sale_validation + relativedelta(months=self.transaction_control_months) < fields.Date.today():
                    partner.last_update_sale_validation = fields.Date.today()
            if partner.last_update_purchase_validation:
                if partner.last_update_purchase_validation + relativedelta(months=self.transaction_control_months_p) < fields.Date.today():
                    partner.last_update_purchase_validation = fields.Date.today()

    def action_last_update_sale_validation(self):
        view_id = self.env.ref('partner_transaction_limit.transaction_limit_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.id,
            'view_type': 'form',
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_last_update_sale_validation': fields.Date.today(),
            }
        }


    def action_last_update_purchase_validation(self):
        view_id = self.env.ref('partner_transaction_limit.transaction_limit_form_p').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'form',
            'res_id': self.id,
            'view_type': 'form',
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_last_update_purchase_validation': fields.Date.today(),
            }
        }
