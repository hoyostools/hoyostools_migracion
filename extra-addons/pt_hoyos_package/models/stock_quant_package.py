from odoo import api, fields, models, tools, _


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    picking_id = fields.Many2one('stock.picking', 'Picking', ondelete='cascade', index=True, copy=False)



