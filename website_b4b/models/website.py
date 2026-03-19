from odoo import api, fields, models


class Website(models.Model):
    _inherit = 'website'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    def _get_warehouse_available_main_company(self, company_id):
        return (
            self.env['ir.default'].sudo()._get('sale.order', 'warehouse_id', company_id=company_id.id) or
            self.env['stock.warehouse'].sudo().search([('company_id', '=', company_id.id)], limit=1).id
        )

    def _get_product_available_qty(self, product):
        main_company = self.env['res.company'].sudo().search([('is_main', '=', True)])
        if main_company.id in product.company_ids.ids and self.env.company.stock_hoyos:
            own_free_qty = product.with_context(warehouse=self._get_warehouse_available()).free_qty
            hoyos_free_qty = product.with_context(warehouse=self._get_warehouse_available_main_company(main_company)).with_company(main_company.id).free_qty
            stock_quantity = own_free_qty + hoyos_free_qty
        else:
            stock_quantity = super()._get_product_available_qty(product)
        return stock_quantity

