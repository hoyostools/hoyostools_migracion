from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request

class WebsiteSaleInherit(WebsiteSale):

    def cart(self, access_token=None, revive='', **post):

        res = super(WebsiteSaleInherit, self).cart(access_token, revive, **post)

        sale_order = request.website.sale_get_order()
        if sale_order:
            for line in sale_order.order_line:
                product = line.product_id
                if not request.env.user._is_public() and product.applicable_web and product.valor_a and product.valor_b:
                    qty = line.product_uom_qty
                    if qty >= product.valor_b and qty <= product.valor_a:
                        line.discount = product.descuento_rango
                    elif qty > product.valor_a and product.descuento_mayor:
                        line.discount = product.descuento_mayor
                    else:
                        line.discount = 0

        return res

    def confirm_order(self, **post):
        res = super(WebsiteSaleInherit, self).confirm_order(**post)

        sale_order = request.website.sale_get_order()
        if sale_order:
            for line in sale_order.order_line:
                product = line.product_id
                if not request.env.user._is_public() and product.applicable_web and product.valor_a or product.valor_b:
                    qty = line.product_uom_qty
                    if qty >= product.valor_b and qty <= product.valor_a:
                        line.discount = product.descuento_rango
                    elif qty > product.valor_a and product.descuento_mayor:
                        line.discount = product.descuento_mayor
                    else:
                        line.discount = 0

        return res