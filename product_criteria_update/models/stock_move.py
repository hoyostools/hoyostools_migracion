from odoo import models, fields, api
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = "stock.move"

    product_criteria_update_finished = fields.Boolean(default=False)
    create_task = fields.Boolean(default=False)

    def finish_criteria_update(self):
        picking_id = self.env['stock.move'].search([(self.env.context['active_domain'][0])])[0].picking_id
        resupply_data = self.env['stock.warehouse.orderpoint'].search([('origin_of_creation', '=', picking_id.id)])
        total = len(picking_id.move_ids)
        finished = 0
        for move_id in picking_id.move_ids:
            if move_id.product_criteria_update_finished:
                finished += 1
        if total == finished:
            picking_id.product_criteria_update_finished = True
            user_ids = self.env['user.criteria.update'].search([])
            users = {}
            for user in user_ids:
                users[user.user_id.id] = len(self.env["stock.warehouse.orderpoint"].search([('assigned', '=', user.user_id.id), ('task_finished', '=', False)]))
            for resupply in resupply_data:
                if user_ids:
                    if resupply.location_id and resupply.location_id.complete_name.lower() == 'clh/existencias/u05/pasillo 01/sin regla abastecer u05':
                        if resupply.route_id and resupply.route_id.name.lower() == 'yumbo: abastecer u05':
                            min_tasks = min(users.values())
                            id_user = [key for key, value in users.items() if value == min_tasks][0]
                            resupply.assigned = self.env["res.users"].search([('id', '=', id_user)])
                            users[id_user] += 1
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'res_id': picking_id.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "No se han revisado todos los productos.",
                    'type': 'warning',
                    'sticky': False,
                }
            }

    def product_criteria_update(self):
        temporal_model_packaging_ids = self.env["temporal.product.packaging"]
        temporal_model_packaging_ids.search([]).unlink()
        model_product_criteria = self.env['product.criteria.update']
        model_product_criteria.search([]).unlink()
        packaging_ids = False
        sale_line_warn_msg = ""
        location_id = True
        route_id = False
        create_replenishment_rule = True
        line_rr = False
        for packaging_id in self.product_id.packaging_ids:
            sale_line_warn_msg += str(packaging_id.name) + " " + str(packaging_id.qty) + "\n"
            new_packaging_id = temporal_model_packaging_ids.create({
                'name': packaging_id.name,
                'product_id': packaging_id.product_id.id,
                'product_uom_id': packaging_id.product_uom_id.id,
                'id_origin': packaging_id.id,
                'package_type_id': packaging_id.package_type_id.id,
                'qty': packaging_id.qty,
                'barcode': packaging_id.barcode,
                'route_ids': packaging_id.route_ids,
                'purchase': packaging_id.purchase,
                'sales': packaging_id.sales,
                'company_id': packaging_id.company_id.id
            })
            if not packaging_ids:
                packaging_ids = new_packaging_id
            else:
                packaging_ids += new_packaging_id
        for route in self.product_id.route_ids:
            if route.name and route.name.lower() == 'yumbo: abastecer u05':
                location_id = False
                route_id = False
                create_replenishment_rule = False
        if location_id:
            location_id = self.env["stock.location"].search([('complete_name', '=', 'CLH/Existencias/U05/Pasillo 01/Sin Regla Abastecer U05')])
            warehouse_id = self.env["stock.warehouse"].search([('code', '=', 'CLH')])
            for route in self.env["stock.route"].search([]):
                if route.name and route.name.lower() == 'yumbo: abastecer u05':
                    route_id = route
            self.create_task = True
            if not location_id:
                raise UserError("No existe la ubicación CLH/Existencias/U05/Pasillo 01/Sin Regla Abastecer U05")
            if not route_id:
                raise UserError("No existe la ruta Yumbo: Abastecer u05")
            line_rr = self.env['temporal.stock.warehouse.orderpoint'].create({
                'product_id': self.product_id.id,
                'route_id': route_id.id if route_id else False,
                'location_id': location_id.id if location_id else self.location_id.id,
                'warehouse_id': warehouse_id.id if warehouse_id else self.warehouse_id.id,
            })
        product_criteria_criteria = model_product_criteria.create({
            'product_id': self.product_id.id,
            'stock_move_id': self.id,
            'picking_id': self.picking_id.id,
            'barcode': self.product_id.barcode,
            'barcode_readonly': True if self.product_id.barcode else False,
            'manufacturer_pref': self.product_id.manufacturer_pref,
            'packaging_ids': packaging_ids,
            'sale_line_warn': 'warning',
            'sale_line_warn_msg': sale_line_warn_msg if sale_line_warn_msg else self.product_id.sale_line_warn_msg,
            'image_1920': self.product_id.image_1920,
            'create_replenishment_rule': create_replenishment_rule,
            'rearrangement_rules': line_rr
        })
        return {
            'name': self.product_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.criteria.update',
            'view_mode': 'form',
            'view_id': self.env.ref('product_criteria_update.product_criteria_update_form_view').id,
            'res_id': product_criteria_criteria.id,
            'target': 'new',
        }