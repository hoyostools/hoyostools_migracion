from odoo import models, fields, api
from odoo.exceptions import UserError

class StockTransferWizardLine(models.TransientModel):
    _name = 'stock.transfer.wizard.line'

    wizard_id = fields.Many2one('stock.transfer.wizard')

    product_id = fields.Many2one('product.product', readonly=True)
    location_id = fields.Many2one('stock.location', readonly=True)

    available_qty = fields.Float(string="Disponible", readonly=True)

    qty_to_move = fields.Float(string="Cantidad a trasladar", required=True)

    location_dest_id = fields.Many2one(
        'stock.location',
        string="Ubicación destino",
        required=True
    )

    @api.constrains('qty_to_move')
    def _check_qty(self):
        for rec in self:
            if rec.qty_to_move > rec.available_qty:
                raise UserError("Cantidad mayor a la disponible")
