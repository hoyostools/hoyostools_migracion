from odoo import models, fields, api
from datetime import timedelta, datetime


class AccountMove(models.Model):
    _inherit = 'account.move'

    financial_discount_percentage = fields.Float(
        string='% Descuento Financiero',
        store=True
    )
    maximum_date_financial_discount = fields.Integer(string="Días Máximo para Descuento Financiero", store=True)
    financial_discount_deadline = fields.Date(
        string="Fecha Límite Descuento Financiero",
        store=True
    )
    
    def create(self, vals):
        if type(vals) == dict and 'invoice_origin' in vals:
            purchase_order = self.env['purchase.order'].search([('name', '=', vals['invoice_origin'])])
            if purchase_order:
                vals['financial_discount_percentage'] = purchase_order.financial_discount_percentage
                vals['maximum_date_financial_discount'] = purchase_order.maximum_date_financial_discount
                vals['financial_discount_deadline'] = datetime.now() + timedelta(
                    days=purchase_order.maximum_date_financial_discount)
        return super(AccountMove, self).create(vals)

    
    @api.onchange('invoice_line_ids')
    def get_financial_discount(self):
        for move in self:
            move.financial_discount_percentage = move.invoice_line_ids.purchase_order_id.financial_discount_percentage
            move.maximum_date_financial_discount = move.invoice_line_ids.purchase_order_id.maximum_date_financial_discount

    @api.onchange('invoice_date', 'maximum_date_financial_discount')
    def _compute_deadline_date_financial_discount(self):
        for move in self:
            if move.invoice_date and move.maximum_date_financial_discount:
                move.financial_discount_deadline = move.invoice_date + timedelta(
                    days=move.maximum_date_financial_discount)
            else:
                move.financial_discount_deadline = False




