from odoo import models, fields, api

class StockInventoryAdjustmentReason(models.Model):
    _name = 'stock.inventory.adjustment.reason'
    _description = 'Motivo de Ajuste de Inventario'

    name = fields.Char(string='Motivo', required=True)

class StockInventoryAdjustmentName(models.TransientModel):
    _inherit = 'stock.inventory.adjustment.name'

    adjustment_reason_id = fields.Many2one(
        'stock.inventory.adjustment.reason',
        string='Motivo de Ajuste',
        required=False
    )
    
    observacion = fields.Char(string='Observación')

    @api.onchange('adjustment_reason_id', 'observacion')
    def _onchange_adjustment_fields(self):
        motivo = self.adjustment_reason_id.name if self.adjustment_reason_id else ''
        obs = self.observacion or ''
        # Concatenamos ambos si existen
        if motivo and obs:
            self.inventory_adjustment_name = f'{motivo} - {obs}'
        elif motivo:
            self.inventory_adjustment_name = motivo
        elif obs:
            self.inventory_adjustment_name = obs
        else:
            self.inventory_adjustment_name = ''
