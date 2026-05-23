from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        """
        Al confirmar una factura de proveedor:
        - Si existe payment_reference:
            coloca ese valor en el campo 'name' (Etiqueta)
            de todos los apuntes contables.
        - Si no existe:
            mantiene el comportamiento nativo de Odoo.
        """
        res = super().action_post()

        for move in self:
            # Solo facturas/proveedores
            if move.move_type in ("in_invoice", "in_refund"):
                if move.payment_reference:
                    move.line_ids.write({
                        "name": move.payment_reference
                    })

        return res

