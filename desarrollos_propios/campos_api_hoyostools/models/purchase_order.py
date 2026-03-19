from odoo import models
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        for order in self:
            # Validamos productos de la orden
            productos_api = order.order_line.filtered(
                lambda line: line.product_id
                and line.product_id.product_tmpl_id.creado_api
            )

            if productos_api:
                nombres = "\n".join(
                    productos_api.mapped('product_id.display_name')
                )
                raise UserError(
                    "❌ No se puede confirmar la orden de compra.\n\n"
                    "Los siguientes productos fueron creados por API y deben ser revisados:\n\n%s"
                    % nombres
                )

        return super().button_confirm()