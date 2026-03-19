from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        for picking_id in self:
            if picking_id.purchase_id and not picking_id.purchase_id.approved_for_processing:
                raise UserError(f"La orden de compra {picking_id.purchase_id.name} asociada al albarán no ha sido"
                                f" aprobada para procesar")
        return super(StockPicking, self).button_validate()