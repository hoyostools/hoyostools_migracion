# -*- coding: utf-8 -*-
# Controller for managing portal sale developed by E Mohamed Eldeeb phone no. +2011136978.

import base64
import logging

from odoo import fields, http, _
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

_logger = logging.getLogger(__name__)


class PortalSale(CustomerPortal):

##################################################################################
    def quotes_get_page_view_values(self, quotation, access_token, **kwargs):
        values = {
            'page_name': 'create_quotation',
            'quotation': quotation,
        }
        return self._get_page_view_values(quotation, access_token, values, 'my_quotation_requests_history', False, **kwargs)


    @http.route(['/my/quotes/<int:quote_id>/delete'], type='http', auth="user", website=True, csrf=False)
    def portal_delete_my_quote(self, quote_id=None, access_token=None, **kw):
        quote_sudo = request.env['sale.order'].sudo()
        redirect = ("/my/quotes/"+str(quote_id))
        try:
            quote_sudo.browse(quote_id).unlink()
        except Exception as e:
            return request.redirect("%s?error_msg=%s" % (redirect, (quote_sudo.error_msg(e))))

        return request.redirect("/my/quotes")

    @http.route(['/my/quotes/create','/my/orders/create'], type='http', auth="user", website=True)
    def portal_create_my_quotes(self,**kw):
        if request.env.user.partner_id.is_seller:
            quotes = request.env['sale.order'].sudo()
            redirect = ("/my/quotes")
            try:
                values = self.get_sale_qoutation_values()
                values.update({'page_name': 'quotes_create'})
                return request.render("portal_sales_management.portal_my_quotes_create", values)
            except Exception as e:
                return request.redirect("%s?error_msg=%s" % (redirect, (quotes.error_msg(e))))
        else:
            return False

    def get_sale_qoutation_values(self):
        values = {}
        product = request.env['product.product'].sudo().search([('sale_ok', '=', True), ('company_ids', 'in', request.env.company.ids)]).mapped(lambda r: {'id':r.id , 'name':r.display_name})
        partner_ids = request.env['res.partner'].sudo().search(['|', ('company_id', '=', request.env.company.id), ('company_id', '=', False)]).mapped(lambda r: {'id':r.id , 'name':r.name})
        #product_ids = request.env['res.partner'].sudo().search([('user_id', '=', request.env.user.id)]).mapped(lambda r: {'id':r.id , 'name':r.name})
        pricelist_ids = request.env['product.pricelist'].sudo().search(['|', ('company_id', '=', False),('company_id', '=', request.env.company.id)]).mapped(lambda r: {'id':r.id , 'name':r.name})
        values.update({
            'product_ids': product,
            'partner_ids': partner_ids,
            'pricelist_ids': pricelist_ids,
        })
        return values


    @http.route('/portal_sales/add/row', type='json', auth="public", methods=['POST'], website=True)
    def portal_sales_job_row(self, **kwargs):
        values = {
            'product_ids': request.env['product.product'].sudo().search([('sale_ok', '=', True), ('company_ids', 'in', request.env.company.ids)]).mapped(lambda r: {'id':r.id , 'name':r.display_name})
            }
        data = request.env['ir.ui.view']._render_template(
            "portal_sales_management.add_new_line", values)
        return {'data': data, 'type': 'professional'}

    def create_document(self, attached_files, quote_id):
        for file in attached_files:
            ufile = file.read()
            vals = {
                'res_model': 'sale.order',
                'res_id': quote_id,
                'datas': base64.b64encode(ufile),
                'type': 'binary',
                'name': file.filename
            }
            if file.filename:
                request.env['ir.attachment'].sudo().create(vals)

    def _prepare_quotations_domain(self, partner):
        return ['|','&',
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['sent', 'cancel']),
            '&',
            ('state','=','draft'),
            ('user_id', '=', request.env.user.id)
        ]

