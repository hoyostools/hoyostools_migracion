# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import operator

class OutstandingPayment(models.TransientModel):
    _name = 'outstanding.payment'
    _description = 'OutstandingPayment'

    partner_id = fields.Many2one('res.partner', string='Partner',required=True, readonly=True)
    outstanding_move_ids = fields.One2many('outstanding.account.move', 'outstanding_pyament_id', string="Moves")
    outstanding_payment_ids = fields.One2many('outstanding.account.payment', 'outstanding_pyament_id', string="Payments kk")
    to_be_paid_amount = fields.Float("To be Paid Total Amount", readonly=True)
    move_type = fields.Selection([
        ('entry', 'Journal Entry'),
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('out_receipt', 'Sales Receipt'),
        ('in_receipt', 'Purchase Receipt'),
        ], readonly=True)

    @api.onchange('outstanding_move_ids')
    def _onchange_outstanding_move_ids(self):
        if self.outstanding_move_ids:
            if any(outstanding_move_id.select_to_pay == True for outstanding_move_id in self.outstanding_move_ids):
                outstanding_move_ids = self.outstanding_move_ids.filtered(lambda l: l.select_to_pay == True)
            else:
                outstanding_move_ids = self.outstanding_move_ids
            self.to_be_paid_amount = sum(outstanding_move_ids.mapped('paid_amount'))

    @api.model
    def default_get(self, fields):
        res = super(OutstandingPayment, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        if active_ids:
            moves = self.env['account.move'].browse(active_ids)
            #print("\nmoves:",moves)
            
            if moves:
                moves = moves.sorted(key=lambda r: (r.invoice_date))#, r.name
                states = moves.mapped('state')
                payment_state = moves.mapped('payment_state')
                partner_ids = moves.mapped('partner_id')
                currency_ids = moves.mapped('currency_id')
                move_types = moves.mapped('move_type')
                #State
                if len(set(states)) > 1:
                    raise UserError(_("Selected all the records state needs to be 'Posted'."))
                elif len(set(states)) == 1 and states[0] == 'posted':
                    pass
                else:
                    raise UserError(_("The Status must be 'Posted'."))
                #Partner
                if len(set(partner_ids)) > 1:
                    raise UserError(_("Multiple Partners Found! Your can reconcile outstanding payments for unique Partner."))
                else:
                    pass
                #payment state
                if 'paid' in payment_state or any(move.amount_residual == 0.00 for move in moves):
                    raise UserError(_("Already Paid record not allowed for Reconcile."))
                #currency_ids
                if len(set(currency_ids)) > 1:
                    raise UserError(_("The Currency must be Same."))
                else:
                    pass

            res.update({'move_type':move_types[0]})

            #ADD MOVE LINES
            move_line_vals = []
            for move in moves:
                move_line_vals.append((0,0,{
                    'name': move.name,
                    'account_move_id': move.id,
                    'paid_amount': move.amount_residual,
                }))

            payment_type = False
            if move_types[0] in ['in_invoice','out_refund']:
                payment_type = 'outbound'
            if move_types[0] in ['out_invoice','in_refund']:
                payment_type = 'inbound'
            payments = self.env["account.payment"].search([('is_reconciled','=',False),('partner_id','=',partner_ids.id), ('currency_id','=',currency_ids.id),('payment_type','=',payment_type), ('state','=','posted')])
            #ADD PAYMENTS Lines
            payment_line_vals = []
            payments = payments.sorted(key=lambda r: (r.date))
            for payment in payments:
                #move is invoice/bill
                if move_types[0] in ['in_invoice','out_invoice']:
                    #avoid payments who paid for credit/debit note and then credit/debit reset to draft
                    if payment.payment_type == 'inbound':#receive
                        #print("receive")
                        pay_term_lines = payment.move_id.line_ids\
                        .filtered(lambda line: line.account_id.account_type in ('asset_receivable'))
                        if not pay_term_lines:
                            continue
                    if payment.payment_type == 'outbound':#send
                        #print("send")
                        pay_term_lines = payment.move_id.line_ids\
                        .filtered(lambda line: line.account_id.account_type in ('liability_payable'))
                        if not pay_term_lines:
                            continue
                #move is credit/debit note
                if move_types[0] in ['in_refund','out_refund']:
                    #add payments who paid for credit/debit note and then credit/debit reset to draft
                    #and also avoid normal or manual payment
                    if payment.payment_type == 'inbound':#receive
                        #print("receive")
                        pay_term_lines = payment.move_id.line_ids\
                        .filtered(lambda line: line.account_id.account_type in ('liability_payable'))
                        if not pay_term_lines:
                            continue
                    if payment.payment_type == 'outbound':#send
                        #print("send")
                        pay_term_lines = payment.move_id.line_ids\
                        .filtered(lambda line: line.account_id.account_type in ('asset_receivable'))
                        if not pay_term_lines:
                            continue
                payment_line_vals.append((0,0,{
                    'name': payment.name,
                    'account_payment_id':payment.id,
                    'is_payment':True
                }))
            #MOVE is invoice/bill then add unpaid credit/debit note in (ADD)PAYMENT Lines
            recon_credit_debit_lst = []
            if move_types[0] in ['in_invoice','out_invoice']:
                for move in moves:
                    if move.invoice_outstanding_credits_debits_widget:
                        content = move.invoice_outstanding_credits_debits_widget.get('content')
                        content = sorted(content, key=operator.itemgetter('date'))
                        for line in content:
                            if line.get('account_payment_id') == False:
                                recon_move = self.env["account.move"].browse(line.get('move_id'))
                                if recon_move.currency_id.id != currency_ids.id:
                                    continue
                                if recon_move.id not in recon_credit_debit_lst:
                                    if recon_move.move_type == 'entry':#JE
                                        date = recon_move.date
                                    else:
                                        date = recon_move.invoice_date
                                    payment_line_vals.append((0,0,{
                                        'name': recon_move.name,
                                        'account_move_id':recon_move.id,
                                        'is_invoice': True,
                                        #'date': recon_move.invoice_date,
                                        'date': date,
                                        'ref' : recon_move.ref,
                                        'move_id' : recon_move.journal_id.id,
                                        'amount' : recon_move.amount_total,
                                    }))
                                    recon_credit_debit_lst.append(recon_move.id)
            
            recon_move_lst = []
            #move is credit/debit note then directly reconcile entry set in (ADD)PAYMENT Lines
            if move_types[0] in ['out_refund','in_refund']:
                for move in moves:
                    if move.invoice_outstanding_credits_debits_widget:
                        content = move.invoice_outstanding_credits_debits_widget.get('content')
                        content = sorted(content, key=operator.itemgetter('date'))
                        for line in content:
                            if line.get('account_payment_id') == False:
                                recon_move = self.env["account.move"].browse(line.get('move_id'))
                                if recon_move.currency_id.id != currency_ids.id:
                                    continue
                                if recon_move.id not in recon_move_lst:
                                    if recon_move.move_type == 'entry' and not recon_move.amount_residual:#JE
                                        amount = recon_move.amount_total
                                    else:
                                        amount = recon_move.amount_residual
                                    payment_line_vals.append((0,0,{
                                        'name': recon_move.name,
                                        'account_move_id':recon_move.id,
                                        'is_invoice': True,
                                        'date': recon_move.invoice_date,
                                        'ref' : recon_move.ref,
                                        'move_id' : recon_move.journal_id.id,
                                        #'amount' : recon_move.amount_residual,
                                        'amount' : amount,
                                    }))
                                    recon_move_lst.append(recon_move.id)
                                
            if not payments and len(payment_line_vals) == 0:
                raise UserError(_("Not found any Payment for '%s'.",partner_ids.name))
            res.update({
                'partner_id': partner_ids.id,
                'outstanding_move_ids': move_line_vals,
                'outstanding_payment_ids':payment_line_vals,
            })
        return res

    def reconcile_payment(self):
        if any(outstanding_move_id.select_to_pay == True for outstanding_move_id in self.outstanding_move_ids):
            outstanding_move_ids = self.outstanding_move_ids.filtered(lambda l: l.select_to_pay == True)
        else:
            outstanding_move_ids = self.outstanding_move_ids
        for outstanding_move_id in outstanding_move_ids:
            if outstanding_move_id.paid_amount and outstanding_move_id.amount_residual:
                if outstanding_move_id.paid_amount > outstanding_move_id.amount_residual:
                    raise UserError(_("To be paid amount can not be greater than due amount."))
        
        #total_move_amounts = sum(outstanding_move_ids.mapped('paid_amount'))
        outstanding_payment_ids = self.outstanding_payment_ids.filtered(lambda l: l.select_to_pay == True)
        if outstanding_payment_ids:
            payment_ids = outstanding_payment_ids.mapped('account_payment_id')
            reconcile_move_ids = outstanding_payment_ids.mapped('account_move_id')
        else:
            outstanding_payment_ids = self.outstanding_payment_ids
            payment_ids = self.outstanding_payment_ids.mapped('account_payment_id')
            reconcile_move_ids = self.outstanding_payment_ids.mapped('account_move_id')
        #first payment
        for payment_id in payment_ids:
            for outstanding_move_id in outstanding_move_ids:
                move = outstanding_move_id.account_move_id
                paid_amount = outstanding_move_id.paid_amount
                ###default
                if move.move_type == 'entry' or move.is_outbound():
                    sign = 1
                else:
                    sign = -1
                ###
                for line in move.invoice_outstanding_credits_debits_widget.get('content'):
                    if line.get('account_payment_id') == payment_id.id and payment_id.is_reconciled == False and paid_amount:
                        opp_reconcile_id = line.get('id')
                        ln = self.env["account.move.line"].browse(opp_reconcile_id)
                        if abs(ln.amount_residual_currency) > paid_amount:
                            amount_residual_currency = sign * paid_amount
                        else:
                            amount_residual_currency = ln.amount_residual_currency
                        
                        if abs(ln.amount_residual) > paid_amount:
                            amount_residual = sign * paid_amount
                        else:
                            amount_residual = ln.amount_residual
                        ln.amount_residual_currency = amount_residual_currency
                        ln.amount_residual = amount_residual
                        move.js_assign_outstanding_line(opp_reconcile_id)
                        #multiple move has partial payment and assign amount is fully paid then,
                        # not repeate for 2nd payment
                        if abs(amount_residual) == paid_amount:
                            outstanding_move_ids -= outstanding_move_id
                        paid_amount -= abs(amount_residual)
                        outstanding_move_id.paid_amount -= abs(amount_residual)
                        
        #second move is credit debit note
        #print("\n\n****second move is credit debit note")
        #print("reconcile_move_ids==>>",reconcile_move_ids)
        #print("outstanding_move_ids==>>",outstanding_move_ids)
        #sss
        for reconcile_move_id in reconcile_move_ids:
            for outstanding_move_id in outstanding_move_ids:
                if not outstanding_move_id.account_move_id.amount_residual:
                    continue
                
                if reconcile_move_id.move_type == 'entry' and not reconcile_move_id.amount_residual:#JE
                    pass
                else:
                    if not reconcile_move_id.amount_residual:
                        break
                move = outstanding_move_id.account_move_id
                paid_amount = outstanding_move_id.paid_amount
                ###default
                if move.move_type == 'entry' or move.is_outbound():
                    sign = 1
                else:
                    sign = -1
                ###
                for line in move.invoice_outstanding_credits_debits_widget.get('content'):
                    #move is credit debit note
                    if line.get('account_payment_id') == False and paid_amount:
                        if line.get('move_id') == reconcile_move_id.id:
                            opp_reconcile_id = line.get('id')
                            ln = self.env["account.move.line"].browse(opp_reconcile_id)

                            if abs(ln.amount_residual_currency) > paid_amount:
                                amount_residual_currency = sign * paid_amount
                            else:
                                amount_residual_currency = ln.amount_residual_currency

                            if abs(ln.amount_residual) > paid_amount:
                                amount_residual = sign * paid_amount
                            else:
                                amount_residual = ln.amount_residual
                            ln.amount_residual_currency = amount_residual_currency
                            ln.amount_residual = amount_residual
                            move.js_assign_outstanding_line(opp_reconcile_id)
                            #multiple move has partial payment and assign amount is fully paid then,
                            # not repeate for 2nd payment
                            if abs(amount_residual) == paid_amount:
                                outstanding_move_ids -= outstanding_move_id
                            reconcile_move_ids = reconcile_move_ids.filtered(lambda l: l.amount_residual)
                            paid_amount -= abs(amount_residual)
                            outstanding_move_id.paid_amount -= abs(amount_residual)
        #ssss
        return True

class OutstandingAccountMove(models.TransientModel):
    _name = 'outstanding.account.move'
    _description = 'Outstanding Account Moves'
    
    outstanding_pyament_id = fields.Many2one('outstanding.payment', string='Outstanding Payment',required=True)
    name = fields.Char(string="Number")
    account_move_id = fields.Many2one('account.move', string='Move',required=True)
    ref = fields.Char(string="Reference", related='account_move_id.ref', readonly=True)
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
    paid_amount = fields.Float(string='To be Paid Amount', required=1)
    move_id = fields.Integer("MOve ID",related='account_move_id.id',)
    invoice_date = fields.Date(string="Date",related='account_move_id.invoice_date')

    @api.onchange('paid_amount')
    def _onchange_paid_amount(self):
        if self.paid_amount and self.amount_residual:
            if self.paid_amount > self.amount_residual:
                raise UserError(_("To be paid amount can not be greater than due amount."))


class OutstandingAccountPayment(models.TransientModel):
    _name = 'outstanding.account.payment'
    _description = 'Outstanding Account Payment'
    
    outstanding_pyament_id = fields.Many2one('outstanding.payment', string='Outstanding Payment',required=True)
    name = fields.Char(string="Number")
    account_payment_id = fields.Many2one('account.payment', string='Payments',required=False)
    select_to_pay = fields.Boolean('Select', copy=0)
    date = fields.Date(string='Date', required=True, related="account_payment_id.date")
    ref = fields.Char(string="Reference", related='account_payment_id.ref', readonly=True)
    move_id = fields.Many2one('account.move', string="Journal", related='account_payment_id.move_id', readonly=True)
    currency_id = fields.Many2one( comodel_name='res.currency', string='Currency', related='account_payment_id.currency_id', readonly=True)
    amount = fields.Monetary(string="Amount", related='account_payment_id.amount', readonly=True)
    state = fields.Selection(related='account_payment_id.state', readonly=True,)
    is_payment = fields.Boolean("Payment", readonly="1")
    is_invoice = fields.Boolean("Credit/Debit",readonly="1")
    account_move_id = fields.Many2one('account.move', string='Move',required=False)
    amount_due = fields.Float(compute="_compute_amount_due", string="Remaining Amount")

    def _compute_amount_due(self):
        for rec in self:
            rec.amount_due = 0
            if rec.account_payment_id:
                payment_id = rec.account_payment_id
                
                if payment_id.reconciled_invoice_ids:
                    paid_amount = 0
                    for move in payment_id.reconciled_invoice_ids:
                        if move.invoice_payments_widget:
                            content_lst = move.invoice_payments_widget.get('content')
                            for content in content_lst:
                                if content.get('account_payment_id') == payment_id.id:
                                    paid_amount += content.get('amount')
                    rec.amount_due = rec.amount - paid_amount
                elif payment_id.reconciled_bill_ids:
                    paid_amount = 0
                    for move in payment_id.reconciled_bill_ids:
                        if move.invoice_payments_widget:
                            content_lst = move.invoice_payments_widget.get('content')
                            for content in content_lst:
                                if content.get('account_payment_id') == payment_id.id:
                                    paid_amount += content.get('amount')
                    rec.amount_due = rec.amount - paid_amount
                else:
                    rec.amount_due = rec.amount
                        
            elif rec.account_move_id:
                if rec.account_move_id.move_type == 'entry' and not rec.account_move_id.amount_residual:#JE
                    active_ids = self._context.get('active_ids')
                    moves = self.env['account.move'].browse(active_ids)
                    amount = 0
                    for move in moves:
                        if move.invoice_outstanding_credits_debits_widget:
                            for line in move.invoice_outstanding_credits_debits_widget.get('content'):
                                if line['move_id'] == rec.account_move_id.id:
                                    #print("line['amount']===>>>",line['amount'])
                                    amount = line['amount']
                    rec.amount_due  = amount
                else:
                    rec.amount_due = rec.account_move_id.amount_residual

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
