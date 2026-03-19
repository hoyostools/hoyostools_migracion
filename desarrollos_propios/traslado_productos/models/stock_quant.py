from odoo import models

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def action_open_transfer_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trasladar Producto',
            'res_model': 'stock.transfer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_line_ids': [
                    (0, 0, {
                        'product_id': quant.product_id.id,
                        'location_id': quant.location_id.id,
                        'available_qty': quant.quantity,
                    }) for quant in self
                ]
            }
        }
