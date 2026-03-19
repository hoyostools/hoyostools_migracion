from odoo import models, fields, api


class StockOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    porcentaje_llenado = fields.Float(
        compute="_compute_porcentaje_llenado",
        store=False
    )

    def create(self, vals):
        res = super().create(vals)
        product = res.product_id
        if res.location_id.complete_name != 'CLH/Existencias/U05/Pasillo 01/Sin Regla Abastecer U05':
            records = self.env["auto.location.record"].search([
                ("product_id", "=", product.id),
                ("sin_regla", "=", True)
            ])
            records.write({
                "sin_regla": False,
                "liberado": True
            })
        return res

    def write(self, vals):
        res = super().write(vals)
        product = self.product_id
        if self.location_id.complete_name != 'CLH/Existencias/U05/Pasillo 01/Sin Regla Abastecer U05':
            records = self.env["auto.location.record"].search([
                ("product_id", "=", product.id),
                ("sin_regla", "=", True)
            ])
            records.write({
                "sin_regla": False,
                "liberado": True
            })
        return res

    def _compute_porcentaje_llenado(self):
        for rec in self:

            qty = self.env["stock.quant"]._get_available_quantity(
                rec.product_id,
                rec.location_id
            )

            if rec.product_max_qty:
                rec.porcentaje_llenado = (qty / rec.product_max_qty) * 100
            else:
                rec.porcentaje_llenado = 0