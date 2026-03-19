from odoo import models, fields, api
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    buy_to_resupply_verification = fields.Boolean(compute='resupply_verification')
    product_criteria_update_finished = fields.Boolean(default=False)

    @api.depends('picking_type_id.warehouse_id')
    def resupply_verification(self):
        self.buy_to_resupply_verification = self.picking_type_id.warehouse_id.buy_to_resupply and self.picking_type_code == 'incoming' if self.picking_type_id.warehouse_id else False

    def start_product_criteria_update(self):
        return {
            'name': 'Entrada de inventario',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'view_mode': 'tree',
            'view_id': self.env.ref('product_criteria_update.stock_picking_inherit_product_list_criteria_view_tree').id,
            'domain': [('picking_id', '=', self.id)],
            'target': 'current',
        }

    def create(self, vals):
        if 'product_criteria_update_finished' in vals:
            vals.update({'product_criteria_update_finished': False})
        if 'move_ids' in vals:
            for line in vals['move_ids']:
                if 'product_criteria_update_finished' in str(line[2]):
                    line[2]['product_criteria_update_finished'] = False
        return super(StockPicking,self).create(vals)
