from odoo import models

class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    def button_validate(self):
        res = super().button_validate()

        for cost in self:
            move = cost.account_move_id

            for line in cost.cost_lines:
                if line.contact_id:

                    aml = move.line_ids.filtered(
                        lambda l: line.name in (l.name or '')
                    )

                    aml.write({
                        "partner_id": line.contact_id.id
                    })

        return res