from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    b4b = fields.Boolean(string='B4B', default=False)

    def create(self, values):
        # Add code here
        return super(SaleOrder, self).create(values)

    def _get_cart_and_free_qty(self, product, line=None):
        self.ensure_one()
        if not line and not product:
            return 0, 0

        main_company = self.env['res.company'].sudo().search([('is_main', '=', True)])

        product_id = product or line.product_id

        if main_company.id in product_id.company_ids.ids and self.env.company.stock_hoyos:
            cart_qty = sum(self._get_common_product_lines(line, product).mapped('product_uom_qty'))
            free_qty = self.env['website']._get_product_available_qty(product_id)
        else:
            cart_qty, free_qty = super()._get_cart_and_free_qty(product, line)
        return cart_qty, free_qty


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_max_available_qty(self):
        main_company = self.env['res.company'].sudo().search([('is_main', '=', True)])
        if main_company.id in self.product_id.company_ids.ids and self.env.company.stock_hoyos:
            free_qty = self.env['website']._get_product_available_qty(self.product_id)
            return free_qty - self.product_id._get_cart_qty()
        else:
            return super()._get_max_available_qty()

