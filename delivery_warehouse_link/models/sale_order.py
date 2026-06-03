from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('carrier_id')
    def _onchange_carrier_set_warehouse(self):
        if self.carrier_id and self.carrier_id.warehouse_id:
            self.warehouse_id = self.carrier_id.warehouse_id