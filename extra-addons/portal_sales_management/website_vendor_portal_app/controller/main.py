# -*- coding: utf-8 -*-

from odoo import fields, http, _, SUPERUSER_ID
from odoo.http import request
from odoo.exceptions import AccessError, MissingError, ValidationError
from collections import OrderedDict
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from datetime import datetime, timedelta, date

class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        print("ggggggg")
        values = super()._prepare_home_portal_values(counters)
        values['purchase_count'] = request.env['purchase.order'].sudo().search_count([
            ('state', 'in', ['purchase', 'done', 'cancel']), ('partner_id', '=', request.env.user.partner_id.id)
        ])
        values['rfq_count'] = request.env['purchase.order'].sudo().search_count([
            ('state', 'in', ['draft', 'sent']), ('partner_id', '=', request.env.user.partner_id.id)
        ])
        print(values)
        return values

    def _document_check_access(self, model_name, document_id, access_token=None):
        """Check if current user is allowed to access the specified record.

        :param str model_name: model of the requested record
        :param int document_id: id of the requested record
        :param str access_token: record token to check if user isn't allowed to read requested record
        :return: expected record, SUDOED, with SUPERUSER context
        :raise MissingError: record not found in database, might have been deleted
        :raise AccessError: current user isn't allowed to read requested document (and no valid token was given)
        """
        document = request.env[model_name].browse([document_id])
        document_sudo = document.with_user(SUPERUSER_ID).exists()
        if not document_sudo:
            raise MissingError(_("This document does not exist."))
        try:
            document.sudo().check_access_rights('read')
            document.sudo().check_access_rule('read')
        except AccessError:
            if not access_token or not document_sudo.access_token or not consteq(document_sudo.access_token, access_token):
                raise
        return document_sudo

    @http.route(['/my/quote', '/my/quote/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_quotation_orders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        print('jjjjjjjj')
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        PurchaseOrder = request.env['purchase.order']

        domain = [('state', 'in', ['draft', 'sent']), ('partner_id', '=', partner.id)]


        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'},
            'amount_total': {'label': _('Total'), 'order': 'amount_total desc, id desc'},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [('state', 'in', ['draft', 'sent'])]},
            'rfq': {'label': _('RFQ'), 'domain': [('state', '=', 'draft')]},
            'sent': {'label': _('Sent'), 'domain': [('state', '=', 'sent')]},
        }


        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # count for pager
        purchase_count = PurchaseOrder.sudo().search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/purchase",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=purchase_count,
            page=page,
            step=self._items_per_page
        )
        # search the purchase orders to display, according to the pager data
        orders = PurchaseOrder.sudo().search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_purchases_history'] = orders.ids[:100]
        values.update({
            'date': date_begin,
            'orders': orders.sudo(),
            'page_name': 'quotation',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/quote',
        })

        return request.render("website_vendor_portal_app.portal_my_purchase_quotes", values)

    @http.route(['/my/quote/<int:order_id>'], type='http', auth="public", website=True)
    def portal_my_purchase_quote(self, order_id=None, access_token=None, **kw):

        try:
            order_sudo = self._document_check_access('purchase.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        values = self._purchase_order_get_page_view_values(order_sudo, access_token, **kw)
        values['next_record'] = False
        values['prev_record'] = False


        return request.render("website_vendor_portal_app.portal_my_purchase_quote", values)

    @http.route(['/my/quotes/<int:order_id>/vendor_price'], type='http', auth="public",methods=['POST'],csrf=False, website=True)
    def vendor_price(self, order_id, **kw):
        purchase_order_line = request.env['purchase.order.line'].sudo().browse(order_id)
        date = datetime.strptime(kw.get('date'), '%m/%d/%Y')

        new_qty = kw.get('qty')

        if float(new_qty) > purchase_order_line.product_qty:
            raise ValidationError(f'La cantidad ingresada debe ser menor o igual a {purchase_order_line.product_qty}"')
        else:
            #purchase_order = request.env['purchase.order'].sudo().browse(purchase_order_line.order_id)
            purchase_order_line.sudo().write({
                'vendor_price':kw.get('price'),
                'price_unit': kw.get('price'),
                'delivery_date':date,
                'product_qty':new_qty,
                'description':kw.get('description'),
                'user_change':request.env.user.id,
                'can_update':False,
            })
        return