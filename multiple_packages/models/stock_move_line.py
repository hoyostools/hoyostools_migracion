# Copyright 2026 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def action_open_multiple_pack_wizard(self):
        """Open the 'Multiple Packages' wizard for the current move line."""
        self.ensure_one()

        return {
            "name": "Multiple Packages",
            "type": "ir.actions.act_window",
            "res_model": "multiple.pack.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_move_line_id": self.id,
                "default_quantity_total": self.quantity,
                "has_carrier": bool(self.picking_id.carrier_id),
            },
        }
