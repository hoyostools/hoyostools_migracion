# -*- coding: utf-8 -*-
from odoo import fields, models, api, _ , tools
import psycopg2
from odoo.tools import float_is_zero
import logging
from datetime import datetime, timedelta


_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_cashback = fields.Boolean(string="Diario Cashback")


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_cashback = fields.Boolean(string='Diario Cashback', related='journal_id.is_cashback', readonly=False)


class ResUsersInherit(models.Model):
    _inherit = 'res.partner'

    active_cashback_limit = fields.Boolean(string="Activar Cashback")
    blocking_amount = fields.Integer(string="Cashback Disponible")
    pos_order_ids = fields.One2many('pos.order', 'partner_id', readonly=True)
    custom_cashback = fields.Float('Cashback', compute="_compute_pos_cashback", store=True)
    attended_event = fields.Boolean(string="Asistio al evento")
    over_permision_unreconciled_10 = fields.Boolean(string="Usar cashback con mora",default=False)
    days_unreconciled_10 = fields.Boolean(string="Tiene mora mayor a 10 dias", compute="_compute_days_unreconciled_10")
    multiplier_points = fields.Float(string="Multiplicador", default= 1.0)

    
    def write(self, vals):
        for record in self:
            if 'blocking_amount' in vals:
                old_name = record.blocking_amount
                new_name = vals['blocking_amount']
                message = "Cashback cambio de %s a %s" % (old_name, new_name)
                record.message_post(body=message)
        return super(ResUsersInherit, self).write(vals)


    @api.depends('unreconciled_aml_ids')
    def _compute_days_unreconciled_10(self):
        for record in self:
            ten_days_ago = datetime.today() - timedelta(days=10)
            found = False

            for aml_id in record.unreconciled_aml_ids:
                if aml_id.date_maturity and aml_id.date_maturity <= ten_days_ago.date():
                    found = True
                    break

            record.days_unreconciled_10 = found
                



    @api.depends('pos_order_ids', 'pos_order_ids.state', 'pos_order_ids.amount_paid')
    def _compute_pos_cashback(self):
        for rec in self:
            orders = rec.pos_order_ids.filtered(lambda odr: odr.state == 'draft')
            pos_cashback = sum(odr.amount_total - odr.amount_paid for odr in rec.pos_order_ids)
            rec.custom_cashback = pos_cashback


    def action_view_cashback_detail(self):
        self.ensure_one()
        return {
            'name': 'POS Cashback Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'pos.order',
            'domain': [('id', 'in', self.pos_order_ids.ids), ('state', '=', 'draft')],
        }
    


class POSOrder(models.Model):
    _inherit="pos.order"

    def add_payment(self, data):
        self.ensure_one()
        self.env['pos.payment'].create(data)
        self.amount_paid = sum(self.payment_ids.mapped('amount'))

    def write(self, vals):        
        res = super(POSOrder,self).write(vals)
        for record in self:
            if record.state == 'invoiced' and record.partner_id.active_cashback_limit:
                cashback_payments = record.payment_ids.filtered(lambda pay: pay.payment_method_id.is_cashback)
                for pay in cashback_payments:
                    if record.partner_id.blocking_amount > 0:
                        record.partner_id.blocking_amount -= pay.amount
                    if record.partner_id.blocking_amount < 0:
                        record.partner_id.blocking_amount = 0

                loyalty_program = record.env['loyalty.program'].search([('is_chasback_program','=',True),('active','=',True)], limit=1)

                if loyalty_program:
                    if not cashback_payments:
                        points_to_add = ((record.amount_total - record.amount_tax) / loyalty_program.value_point) * record.partner_id.multiplier_points
                        record.partner_id.blocking_amount += points_to_add

        return res

class SaleOrder(models.Model):
    _inherit="sale.order"

    def action_confirm(self):
        res = super(SaleOrder,self).action_confirm()
        for record in self:
            loyalty_program = record.env['loyalty.program'].search([('is_chasback_program','=',True),('active','=',True)], limit=1)
            if loyalty_program and record.partner_id.active_cashback_limit:
                points_to_add = (record.amount_untaxed / loyalty_program.value_point) * record.partner_id.multiplier_points
                record.partner_id.blocking_amount += points_to_add
        return res





class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    is_chasback_program = fields.Boolean(string="Cashback",default=False)
    value_point = fields.Monetary(string="Valor por punto",default=1000)


class LoyaltyCard(models.Model):
    _inherit = "loyalty.card"