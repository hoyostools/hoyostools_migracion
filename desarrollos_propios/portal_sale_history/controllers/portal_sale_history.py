from odoo import http, fields
from odoo.http import request
from collections import defaultdict
from datetime import timedelta
from odoo.addons.portal.controllers.portal import pager as portal_pager


class PortalSaleHistory(http.Controller):

    @http.route(['/my/sale_history', '/my/sale_history/page/<int:page>'], type='http', auth="user", website=True)
    def portal_sale_history(self, page=1, start_date=None, end_date=None, **kw):

        partner = request.env.user.partner_id

        if not start_date and not end_date:
            end_date = fields.Date.today()
            start_date = end_date - timedelta(days=30)

        domain = [
            ('state','=','sale'),
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date)
        ]

        sale_order = request.env['sale.order'].sudo()

        order_count = sale_order.search_count(domain)

        pager = portal_pager(
            url="/my/sale_history",
            url_args={
                'start_date': start_date,
                'end_date': end_date,
            },
            total=order_count,
            page=page,
            step=5
        )

        # Aquí se aplica la paginación
        orders = sale_order.search(
            domain,
            order="date_order desc",
            limit=5,
            offset=pager['offset']
        )
        all_orders = sale_order.search(
            domain,
            order="date_order desc",
            offset=pager['offset']
        )

        # Rankings
        product_counter = defaultdict(float)
        category_counter = defaultdict(float)

        for order in all_orders:
            for line in order.order_line:

                product_counter[line.product_id] += line.product_uom_qty

                if line.product_id.categ_id:
                    category_counter[line.product_id.categ_id] += line.product_uom_qty

        top_products = sorted(
            [{"name": p.name, "qty": q, "id": p.id} for p, q in product_counter.items()],
            key=lambda x: x["qty"],
            reverse=True
        )[:10]

        page_products = int(kw.get('page_products', 1))
        step_products = 5

        total_products = len(top_products)

        pager_products = portal_pager(
            url="/my/sale_history",
            url_args={
                'start_date': start_date,
                'end_date': end_date,
            },
            total=total_products,
            page=page_products,
            step=step_products
        )

        offset_products = pager_products['offset']

        top_products_page = top_products[offset_products:offset_products + step_products]

        top_categories = sorted(
            [{"id": c.id, "name": c.name, "qty": q} for c, q in category_counter.items()],
            key=lambda x: x["qty"],
            reverse=True
        )[:10]

        max_qty = top_categories[0]["qty"] if top_categories else 1

        for cat in top_categories:
            cat["percent"] = (cat["qty"] / max_qty) * 100

        last_month = fields.Datetime.now() - timedelta(days=30)

        new_products = request.env['product.template'].sudo().search([
            ('create_date', '>=', last_month),
            ('sale_ok', '=', True),
            ('list_price', '>', 0),
            ('fecha_recepcion', '!=', False),
        ], order="create_date desc")

        categories = request.env['product.brand'].sudo().search([('id', 'in', new_products.product_brand_id.ids)])

        values = {
            'orders': orders,
            'pager': pager,
            'pager_products': pager_products,
            'start_date': start_date,
            'end_date': end_date,
            'top_products': top_products_page,
            'top_categories': top_categories,
            'new_products': new_products,
            'categories': categories,
        }
        return request.render('portal_sale_history.portal_sale_history_page', values)

    @http.route('/my/reorder/<int:order_id>', type='http', auth='user', website=True)
    def portal_reorder(self, order_id, **kw):

        order = request.env['sale.order'].sudo().browse(order_id)

        new_order = order.copy({
            'state': 'draft'
        })

        return request.redirect('/my/orders/%s' % new_order.id)

    @http.route('/my/filter_products', type='json', auth="user", website=True)
    def filter_products(self, product_brand_id=None):

        last_month = fields.Datetime.now() - timedelta(days=30)

        domain = [
            ('create_date', '>=', last_month),
            ('sale_ok', '=', True),
            ('list_price', '>', 0),
            ('fecha_recepcion', '!=', False),
        ]

        if product_brand_id:
            domain.append(('product_brand_id', '=', int(product_brand_id)))

        products = request.env['product.template'].sudo().search(domain)

        result = []
        for p in products:
            result.append({
                'id': p.product_variant_id.id,
                'name': p.name,
                'price': p.list_price,
                'image': f"/web/image/product.product/{p.product_variant_id.id}/image_1920"
            })

        return result


