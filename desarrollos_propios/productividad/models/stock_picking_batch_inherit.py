from odoo import models

class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    def action_done(self):
        return super().action_done()
