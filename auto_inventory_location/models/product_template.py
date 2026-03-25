from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        res = super().write(vals)
        if 'ubicacion_reab' in vals:
            self._onchange_reab()
        return res

    @api.onchange('ubicacion_reab')
    @api.depends('ubicacion_reab')
    def _onchange_reab(self):
        product = self.env['product.product'].search([('product_tmpl_id', '=', self.product_variant_id.id)])
        if not self.ubicacion_reab or self.ubicacion_reab.complete_name != 'CLH/Existencias/U05/Pasillo 01/Sin Regla Abastecer U05':
            records = self.env["auto.location.record"].search([
                ("product_id", "=", product.id),
                ("sin_regla", "=", True)
            ])
            records.write({
                "sin_regla": False,
                "liberado": True
            })
        else:
            records = self.env["auto.location.record"].search([
                ("product_id", "=", product.id),
                ("sin_regla", "=", True)
            ])
            records.write({
                "sin_regla": True,
                "liberado": False
            })