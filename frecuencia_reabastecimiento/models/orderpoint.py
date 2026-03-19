from odoo import models, fields, api


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res._update_product_reglas()
        return res

    def write(self, vals):
        res = super().write(vals)
        self._update_product_reglas()
        return res

    def _update_product_reglas(self):
        for rec in self:
            if not rec.location_id or not rec.product_id:
                continue

            product = rec.product_id.product_tmpl_id
            location_name = rec.location_id.complete_name or ''

            # =========================
            # CLH
            # =========================
            if 'CLH/Existencias/U05/' in location_name:
                product._compute_reglas()
                product._compute_qty_multiple()
                product._compute_ubicacion_reab()

            # =========================
            # EDI
            # =========================
            if 'EDI/Existencias/U01/' in location_name:
                product._compute_reglas_edi()
                product._compute_qty_multiple_edi()
                product._compute_ubicacion_reab_edi()
                
                
            # =========================
            # PTV
            # =========================
                
            if 'PTV/Existencias' in location_name:
                product._compute_reglas_ptv()
                product._compute_qty_multiple_ptv()
                product._compute_ubicacion_reab_ptv()