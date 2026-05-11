from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    inventario_yumbo = fields.Float(
        string='Inventario Yumbo',
        compute='_compute_custom_stock'
    )

    inventario_cali = fields.Float(
        string='Inventario Cali',
        compute='_compute_custom_stock'
    )

    inventario_ptv = fields.Float(
        string='Inventario PTV',
        compute='_compute_custom_stock'
    )

    @api.depends()
    def _compute_custom_stock(self):

        StockQuant = self.env['stock.quant']

        for product in self:

            product.inventario_yumbo = 0.0
            product.inventario_cali = 0.0
            product.inventario_ptv = 0.0

            variants = product.product_variant_ids.ids

            if not variants:
                continue

            # =========================
            # YUMBO
            # =========================

            yumbo_locations = self.env['stock.location'].search([
                '|',
                ('complete_name', 'ilike', 'CLH/Existencias/U05'),
                ('complete_name', 'ilike', 'CLH/Existencias/Bodegaje')
            ])

            yumbo_quants = StockQuant.search([
                ('product_id', 'in', variants),
                ('location_id', 'in', yumbo_locations.ids)
            ])

            product.inventario_yumbo = sum(
                q.quantity - q.reserved_quantity
                for q in yumbo_quants
            )

            # =========================
            # CALI
            # =========================

            cali_locations = self.env['stock.location'].search([
                ('complete_name', 'ilike', 'EDI/Existencias/U01')
            ])

            cali_quants = StockQuant.search([
                ('product_id', 'in', variants),
                ('location_id', 'in', cali_locations.ids)
            ])

            product.inventario_cali = sum(
                q.quantity - q.reserved_quantity
                for q in cali_quants
            )

            # =========================
            # PTV
            # =========================

            ptv_locations = self.env['stock.location'].search([
                ('complete_name', '=', 'PTV/Existencias')
            ])

            ptv_quants = StockQuant.search([
                ('product_id', 'in', variants),
                ('location_id', 'in', ptv_locations.ids)
            ])

            product.inventario_ptv = sum(
                q.quantity - q.reserved_quantity
                for q in ptv_quants
            )