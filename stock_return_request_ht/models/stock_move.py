from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    qty_returnable = fields.Float(
        digits="Product Unit of Measure",
        string="Returnable Quantity",
        compute="_compute_qty_returnable",
    )

    def _compute_qty_returnable(self):
        """Busca movimientos devueltos encadenados para calcular cuánta cantidad del original se puede devolver."""
        self.qty_returnable = 0
        for move in self.filtered(lambda x: x.state not in ["draft", "cancel"]):
            if not move.returned_move_ids:
                if move.state == "done":
                    move.qty_returnable = move.quantity
                continue
            move.qty_returnable = move.quantity - sum(
                move.returned_move_ids.mapped("qty_returnable")
            )

    def _get_lot_returnable_qty(self, lot_id, qty=0):
        """Busca movimientos devueltos encadenados para calcular cuánta cantidad del original se puede devolver para un lote determinado."""
        for move in self.filtered(lambda x: x.state not in ["draft", "cancel"]):
            mls = move.move_line_ids.filtered(lambda x: x.lot_id == lot_id)
            qty += sum(mls.mapped("quantity"))
            qty -= move.returned_move_ids._get_lot_returnable_qty(lot_id)
        return qty
    
    def _action_assign(self, **kwargs):
        if self.env.context.get("skip_assign_move", False):
            # Evite asignar movimientos de stock permitiendo crear líneas de movimiento de stock manualmente
            return
        return super()._action_assign(**kwargs)
