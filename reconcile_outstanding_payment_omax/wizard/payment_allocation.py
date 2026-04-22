# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ReconcilePayment(models.TransientModel):
    _name = 'reconcile.payment'
    _description = 'Reconcile Payment'

    partner_id = fields.Many2one('res.partner', string='Partner',required=True, readonly=True)
    allocation_move_ids = fields.One2many('reconcile.payment.account.move', 'reconcile_pyament_id', string="Moves")
    allocation_payment_ids = fields.One2many('payment.allocation.account.payment', 'reconcile_pyament_id', string="Payments")
    to_be_paid_amount = fields.Float("To be Paid Amount", readonly=True)
    payment_type = fields.Selection([
        ('outbound', 'Send'),
        ('inbound', 'Receive'),
        ], readonly=True)

    @api.onchange('allocation_move_ids')
    def _onchange_allocation_move_ids(self):
        if self.allocation_move_ids:
            if any(outstanding_move_id.select_to_pay == True for outstanding_move_id in self.allocation_move_ids):
                allocation_move_ids = self.allocation_move_ids.filtered(lambda l: l.select_to_pay == True)
            else:
                allocation_move_ids = self.allocation_move_ids
            self.to_be_paid_amount = sum(allocation_move_ids.mapped('paid_amount'))

    @api.model
    def default_get(self, fields):
        res = super(ReconcilePayment, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        if active_ids:
            payments = self.env['account.payment'].browse(active_ids)
            if payments:
                payments = payments.sorted(key=lambda r: (r.date))
                states = payments.mapped('state')
                partner_ids = payments.mapped('partner_id')
                payment_type = payments.mapped('payment_type')
                currency_ids = payments.mapped('currency_id')
                #State
                if len(set(states)) > 1:
                    raise UserError(_("Selected all the records state needs to be 'Posted'."))
                elif len(set(states)) == 1 and states[0] == 'posted':
                    pass
                else:
                    raise UserError(_("The Status must be 'Posted'."))
                #Partner
                if len(set(partner_ids)) > 1:
                    raise UserError(_("The Partner must be unique."))
                else:
                    pass
                #payment_type
                if len(set(payment_type)) > 1:
                    raise UserError(_("The Payment Type must be Same."))
                else:
                    pass
                #currency_ids
                if len(set(currency_ids)) > 1:
                    raise UserError(_("The Currency must be Same."))
                else:
                    pass
                res.update({'payment_type':payment_type[0]})

            payment_line_vals = []
            for payment in payments:
                if payment.is_reconciled:
                    raise UserError(_("'%s' is already reconciled.",payment.name))
                payment_line_vals.append((0,0,{
                    'name': payment.name,
                    'account_payment_id':payment.id,
                }))
                #find account receivable or payable 
                #based on payment (who paid for credit/debit note and then credit/debit reset to draft) allocation
                # then (only debit/credit note visible)
                pay_term_lines = payment.move_id.line_ids\
                .filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))

            if payment_type[0] == 'inbound':
                move_type = ['out_invoice','in_refund']
                #payment allocation (only Vendor credit note visible)
                if pay_term_lines.account_id.account_type == 'liability_payable':
                    move_type = ['in_refund']
            else:
                move_type = ['in_invoice','out_refund']
                #payment allocation (only Customer credit note visible)
                if pay_term_lines.account_id.account_type == 'asset_receivable':
                    move_type = ['out_refund']
            
            moves = self.env["account.move"].search([('state','=','posted'),('partner_id','=',partner_ids.id),('move_type','in',move_type),('amount_residual','!=',0), ('currency_id','=',currency_ids.id)])
            if not moves:
                raise UserError(_("Not found any Move for '%s'.",partner_ids.name))

            moves = moves.sorted(key=lambda r: (r.invoice_date))
            move_line_vals = []
            for move in moves:
                #move is debit/credit note
                if move.move_type in ['in_refund','out_refund']:
                    #Related debit/credit note add in move lines
                    move_pay_term_lines = move.line_ids\
                        .filtered(lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable'))
                    if move_pay_term_lines:
                        move_account_id = move_pay_term_lines.account_id.id
                    
                    if move_account_id in pay_term_lines.account_id.ids:
                        if move.currency_id.id != currency_ids.id:
                            continue
                        move_line_vals.append((0,0,{
                            'name': move.name,
                            'account_move_id': move.id,
                            'paid_amount': move.amount_residual,
                        }))
                else:
                    #move is inv/bill
                    move_line_vals.append((0,0,{
                        'name': move.name,
                        'account_move_id': move.id,
                        'paid_amount': move.amount_residual,
                    }))

            if len(move_line_vals) == 0:
                raise UserError(_("Not found any Moves for '%s'.",partner_ids.name))
            res.update({
                'partner_id': partner_ids.id,
                'allocation_move_ids': move_line_vals,
                'allocation_payment_ids':payment_line_vals,
            })
        return res

    def reconcile_payment(self):
        if any(allocation_move_id.select_to_pay == True for allocation_move_id in self.allocation_move_ids):
            allocation_move_ids = self.allocation_move_ids.filtered(lambda l: l.select_to_pay == True)
        else:
            allocation_move_ids = self.allocation_move_ids
            
        for allocation_move_id in allocation_move_ids:
            if allocation_move_id.paid_amount and allocation_move_id.amount_residual:
                if allocation_move_id.paid_amount > allocation_move_id.amount_residual:
                    raise UserError(_("To be paid amount can not be greater than due amount."))

        allocation_payment_ids = self.allocation_payment_ids.filtered(lambda l: l.select_to_pay == True)
        if allocation_payment_ids:
            payment_ids = allocation_payment_ids.mapped('account_payment_id')
        else:
            payment_ids = self.allocation_payment_ids.mapped('account_payment_id')
        for payment_id in payment_ids:
            for allocation_move_id in allocation_move_ids:
                if payment_id.is_reconciled:
                    break
                move = allocation_move_id.account_move_id
                paid_amount = allocation_move_id.paid_amount
                ##default
                if move.move_type == 'entry' or move.is_outbound():
                    sign = 1
                else:
                    sign = -1
                ##
                
                for line in move.invoice_outstanding_credits_debits_widget.get('content'):
                    if line.get('account_payment_id') == payment_id.id and paid_amount:
                        opp_reconsile_id = line.get('id')
                        ###
                        ln = self.env["account.move.line"].browse(opp_reconsile_id)
                        
                        #if amount > paid_amount:
                        if abs(ln.amount_residual_currency) > paid_amount:
                            amount_residual_currency = sign * paid_amount
                        else:
                            amount_residual_currency = ln.amount_residual_currency

                        #if amount > paid_amount:
                        if abs(ln.amount_residual) > paid_amount:
                            amount_residual = sign * paid_amount
                        else:
                            amount_residual = ln.amount_residual

                        ln.amount_residual_currency = amount_residual_currency
                        ln.amount_residual = amount_residual
                        
                        move.js_assign_outstanding_line(opp_reconsile_id)
                        #multiple move has partial payment and assign amount is fully paid then,
                        # not repeate for 2nd payment
                        if abs(amount_residual) == paid_amount:
                            allocation_move_ids -= allocation_move_id
                        #deduct paid amount b'cz multiple payment reconcile same amount in record
                        #like move is 400 and 1st 22.5 and 2nd 22.5
                        paid_amount -= abs(amount_residual)
                        allocation_move_id.paid_amount -= abs(amount_residual)
        
        #ssss
        return True

class ReconcilePaymentAccountMove(models.TransientModel):
    _name = 'reconcile.payment.account.move'
    _description = 'Reconcile Payment Moves'
    
    reconcile_pyament_id = fields.Many2one('reconcile.payment', string='Reconcile Payment',required=True)
    name = fields.Char(string="Number")
    account_move_id = fields.Many2one('account.move', string='Move',required=True)
    ref = fields.Char(string="Origin", related='account_move_id.ref', readonly=True)
    company_id = fields.Many2one('res.company', string='Company',related='account_move_id.company_id',)
    due_date = fields.Date(string='Due Date', required=True, related="account_move_id.invoice_date_due")
    company_currency_id = fields.Many2one(string='Company Currency', related='company_id.currency_id', readonly=True)
    amount_untaxed = fields.Monetary( 
        string='Untaxed Amount',
        related='account_move_id.amount_untaxed', readonly=True,
        currency_field='company_currency_id')
    amount_total = fields.Monetary(
        string='Total Amount',
        related='account_move_id.amount_total', readonly=True,
        currency_field='company_currency_id',
    )
    amount_residual = fields.Monetary(
        string='Amount Due',
        related='account_move_id.amount_residual', readonly=True,
        currency_field='company_currency_id',
    )
    state = fields.Selection(related='account_move_id.state', readonly=True,)
    select_to_pay = fields.Boolean('Select', copy=0)
    paid_amount = fields.Float(string='Paid Amount', required=1,)#digits=(12, 3)

    @api.onchange('paid_amount')
    def _onchange_paid_amount(self):
        if self.paid_amount and self.amount_residual:
            if self.paid_amount > self.amount_residual:
                raise UserError(_("To be paid amount can not be greater than due amount."))


class PaymentAllocationAccountPayment(models.TransientModel):
    _name = 'payment.allocation.account.payment'
    _description = 'Payment Allocation Account Payment'
    
    reconcile_pyament_id = fields.Many2one('reconcile.payment', string='Reconcile Payment',required=True)
    name = fields.Char(string="Number")
    account_payment_id = fields.Many2one('account.payment', string='Payments',required=True)
    select_to_pay = fields.Boolean('Select', copy=0)
    date = fields.Date(string='Date', required=True, related="account_payment_id.date")
    ref = fields.Char(string="Reference", related='account_payment_id.ref', readonly=True)
    move_id = fields.Many2one('account.move', string="Journal", related='account_payment_id.move_id', readonly=True)
    currency_id = fields.Many2one( comodel_name='res.currency', string='Currency', related='account_payment_id.currency_id', readonly=True)
    amount = fields.Monetary(string="Amount", related='account_payment_id.amount', readonly=True)
    state = fields.Selection(related='account_payment_id.state', readonly=True,)
    amount_due = fields.Float(compute="_compute_amount_due", string="Remaining Amount")

    def _compute_amount_due(self):
        for rec in self:
            rec.amount_due = 0
            paid_amount = 0
            if rec.account_payment_id:
                payment_id = rec.account_payment_id
                if payment_id.reconciled_invoice_ids:
                    
                    for move in payment_id.reconciled_invoice_ids:
                        if move.invoice_payments_widget:
                            content_lst = move.invoice_payments_widget.get('content')
                            for content in content_lst:
                                if content.get('account_payment_id') == payment_id.id:
                                    paid_amount += content.get('amount')
                    rec.amount_due = rec.amount - paid_amount
                elif payment_id.reconciled_bill_ids:
                    for move in payment_id.reconciled_bill_ids:
                        content_lst = move.invoice_payments_widget.get('content')
                        if move.invoice_payments_widget:
                            for content in content_lst:
                                if content.get('account_payment_id') == payment_id.id:
                                    paid_amount += content.get('amount')
                    rec.amount_due = rec.amount - paid_amount
                else:
                    rec.amount_due = rec.amount

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
