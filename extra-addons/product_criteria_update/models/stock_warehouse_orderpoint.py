from odoo import models, fields, api
from odoo.exceptions import UserError


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    origin_of_creation = fields.Many2one("stock.picking")
    assigned = fields.Many2one("res.users")
    task_finished = fields.Boolean(string="Tarea finalizada", default=False, store=True)
    codigo_barras = fields.Char()
    codigo_barras_location = fields.Char()


    def finish_task(self):
        if not self.product_min_qty:
            raise UserError("No ha indicado la cantidad mínima")
        if not self.product_max_qty:
            raise UserError("No ha indicado la cantidad máxima")
        if self.location_id and self.location_id.complete_name.lower() == 'clh/existencias/u05/pasillo 01/sin regla abastecer u05':
            raise UserError("No se ha actualizado la ubicación")
        self.task_finished = True

    @api.model
    def read_barcode_product(self):
        return {
            'name': "Regla de reordenamiento",
            'type': 'ir.actions.act_window',
            'res_model': 'stock.warehouse.orderpoint',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'product_criteria_update.stock_warehouse_order_point_barcode_view_form').id,
            'target': 'new',
        }