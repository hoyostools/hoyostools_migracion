from odoo import models, fields, api

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    def action_tasks_view(self):
        return {
            'name': "Tareas",
            'type': 'ir.actions.act_window',
            'res_model': 'stock.warehouse.orderpoint',
            'view_mode': 'tree',
            'view_id': self.env.ref(
                'product_criteria_update.stock_warehouse_order_point_criteria_view_tree').id,
            'domain': [('assigned', '=', self.env.user.id)],
            'context': {'search_default_pending_tasks': True},
            'target': 'current',
        }

    def open_reordering_rules(self):
        return {
            'name': "Reglas de reordenamiento",
            'type': 'ir.actions.act_window',
            'res_model': 'stock.warehouse.orderpoint',
            'view_mode': 'tree',
            'view_id': self.env.ref(
                'product_criteria_update.stock_warehouse_order_point_barcode_view_tree').id,
            'target': 'current',
        }
