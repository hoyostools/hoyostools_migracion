# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"


    price_unit_cop = fields.Monetary(string='Unit Price COP', readonly=True,
                                     currency_field='company_currency_id', currency='company_currency_id',compute="_compute_price_unit_cop")

    price_subtotal_cop = fields.Monetary(
        string='Subtotal COP', readonly=True, currency_field='company_currency_id', currency='company_currency_id',compute="_compute_price_subtotal_cop")

    price_total_cop = fields.Monetary(
        string='Total COP', readonly=True, currency_field='company_currency_id', currency='company_currency_id',compute="_compute_price_total_cop")


    def _get_invoice_lines_taxes(self, tax, tax_amount, invoice_line_taxes_total):
        tax_code = tax.tax_group_id.tax_group_type_id.code
        tax_name = tax.tax_group_id.tax_group_type_id.name
        # tax_percent = '{:.2f}'.format(tax_amount)
        tax_percent = str('{:.3f}'.format(tax_amount))

        if tax_code not in invoice_line_taxes_total:
            invoice_line_taxes_total[tax_code] = {}
            invoice_line_taxes_total[tax_code]['total'] = 0
            invoice_line_taxes_total[tax_code]['name'] = tax_name
            invoice_line_taxes_total[tax_code]['taxes'] = {}

        if tax_percent not in invoice_line_taxes_total[tax_code]['taxes']:
            invoice_line_taxes_total[tax_code]['taxes'][tax_percent] = {}
            invoice_line_taxes_total[tax_code]['taxes'][tax_percent]['base'] = 0
            invoice_line_taxes_total[tax_code]['taxes'][tax_percent]['amount'] = 0

        invoice_line_taxes_total[tax_code]['total'] += (
            self.price_subtotal_cop * tax_amount / 100)
        invoice_line_taxes_total[tax_code]['taxes'][tax_percent]['base'] += (
            self.price_subtotal_cop)
        invoice_line_taxes_total[tax_code]['taxes'][tax_percent]['amount'] += (
            self.price_subtotal_cop * tax_amount / 100)

        return invoice_line_taxes_total

    def _get_information_content_provider_party_values(self):
        return {
            'IDschemeID': False,
            'IDschemeName': False,
            'ID': False}


    @api.depends('price_unit', 'currency_id', 'move_id.trm')
    def _compute_price_unit_cop(self):
        for record in self:
            if record.currency_id.name != 'COP':
                record.price_unit_cop = record.price_unit * record.move_id.trm
            else:
                record.price_unit_cop = record.price_unit

    @api.depends('price_subtotal', 'currency_id', 'move_id.trm')
    def _compute_price_subtotal_cop(self):
        for record in self:
            if record.currency_id.name != 'COP':
                record.price_subtotal_cop = record.price_subtotal * record.move_id.trm
            else:
                record.price_subtotal_cop = record.price_subtotal

    @api.depends('price_total', 'currency_id', 'move_id.trm')
    def _compute_price_total_cop(self):
        for record in self:
            if record.currency_id.name != 'COP':
                record.price_total_cop = record.price_total * record.move_id.trm
            else:
                record.price_total_cop = record.price_total
