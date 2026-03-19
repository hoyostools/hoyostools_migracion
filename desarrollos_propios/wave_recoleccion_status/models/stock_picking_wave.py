from odoo import models, fields, api

class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    recoleccion = fields.Boolean(string='Recolección iniciada', compute='_compute_recoleccion', store=True)

    @api.depends('picking_ids.move_line_ids.picked')
    def _compute_recoleccion(self):
        for batch in self:
            batch.recoleccion = False  # por defecto
            for picking in batch.picking_ids:
                for line in picking.move_line_ids:
                    if line.picked:
                        batch.recoleccion = True
                        break
                if batch.recoleccion:
                    break
