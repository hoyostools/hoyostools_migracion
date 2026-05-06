from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _compute_ubicacion_reab(self):
        res = super()._compute_ubicacion_reab()
        for record in self:
            record._onchange_reab()
        return res

    @api.onchange('ubicacion_reab')
    @api.depends('ubicacion_reab')
    @api.constrains('ubicacion_reab')
    def _onchange_reab(self):
        for record in self:
            product = self.env['product.product'].search([('product_tmpl_id', '=', record.product_variant_id.id)])
            if record.ubicacion_reab and record.ubicacion_reab.complete_name != 'CLH/Existencias/U05/Pasillo 01/Sin Regla Abastecer U05':
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
                ])
                records.write({
                    "sin_regla": True,
                    "liberado": False
                })