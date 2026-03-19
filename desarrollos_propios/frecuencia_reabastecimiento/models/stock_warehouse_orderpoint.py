from odoo import models, fields

class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    tunel = fields.Selection(related='location_id.tunel', string='Túnel', store=True, readonly=True)