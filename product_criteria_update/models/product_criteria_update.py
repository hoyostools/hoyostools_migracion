from odoo import models, fields, api
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP
from odoo.exceptions import UserError


class ProductCriteriaWizard(models.TransientModel):
    _name = "product.criteria.update"

    stock_move_id = fields.Many2one("stock.move")
    picking_id = fields.Many2one("stock.picking")
    product_id = fields.Many2one("product.product")
    barcode = fields.Char(string="Código de barras")
    manufacturer_pref = fields.Char(string="Código de producto del fabricante")
    packaging_ids = fields.One2many("temporal.product.packaging", "product_criteria_update", "Embalaje")
    sale_line_warn = fields.Selection(
        WARNING_MESSAGE, string="Sales Order Line",
        help=WARNING_HELP, required=True, default="no-message")
    sale_line_warn_msg = fields.Text(string="Message for Sales Order Line")
    image_1920 = fields.Image("Imagen", readonly=True)
    create_replenishment_rule = fields.Boolean(default=False)
    barcode_readonly = fields.Boolean(default=False)
    rearrangement_rules = fields.One2many("temporal.stock.warehouse.orderpoint", 'criteria')

    @api.onchange('packaging_ids')
    def description_sale_data(self):
        for product_criteria in self:
            product_criteria.sale_line_warn_msg = ""
            for packaging_id in product_criteria.packaging_ids:
                if packaging_id.name and packaging_id.name.lower() in ['caja externa', 'caja master', 'caja máster']:
                    product_criteria.qty_multiple = packaging_id.qty
                product_criteria.sale_line_warn_msg += str(packaging_id.name) + " " + str(packaging_id.qty) + "\n"

    def create_ticket_image(self):
        marketing_team = False
        for record in self.env['helpdesk.team'].search([]):
            if 'publicidad' in record.name.lower() or 'marketing' in record.name.lower():
                marketing_team = record
        if marketing_team:
            self.env["helpdesk.ticket"].create({
                'name': 'Error imagen producto: ' + self.product_id.display_name,
                'team_id': marketing_team.id,
                'user_id': marketing_team.member_ids[0].id if marketing_team.member_ids else False
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "El ticket se ha enviado correctamente.",
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError("No existe el grupo al que se debe asignar el ticket (Publicidad)")

    def error_barcode(self):
        marketing_team = False
        for record in self.env['helpdesk.team'].search([]):
            if 'publicidad' in record.name.lower() or 'marketing' in record.name.lower():
                marketing_team = record
        if marketing_team:
            self.env["helpdesk.ticket"].create({
                'name': 'Error código de barras para el producto: ' + self.product_id.display_name,
                'team_id': marketing_team.id,
                'user_id': marketing_team.member_ids[0].id if marketing_team.member_ids else False
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': "El ticket se ha enviado correctamente.",
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError("No existe el grupo al que se debe asignar el ticket (Publicidad)")

    def action_confirm_verification(self):
        if self.product_id.barcode and self.product_id.barcode != self.barcode:
            return {
                'name': False,
                'type': 'ir.actions.act_window',
                'res_model': 'product.criteria.update',
                'view_mode': 'form',
                'view_id': self.env.ref(
                    'product_criteria_update.product_criteria_update_validation_view').id,
                'res_id': self.id,
                'target': 'new',
            }
        else:
            self.action_confirm()

    def action_confirm(self):
        self.product_id.barcode = self.barcode
        self.product_id.manufacturer_pref = self.manufacturer_pref
        self.product_id.sale_line_warn = self.sale_line_warn
        self.product_id.sale_line_warn_msg = self.sale_line_warn_msg
        self.product_id.packaging_ids = False
        for packaging_id in self.packaging_ids:
            self.product_id.packaging_ids += self.env['product.packaging'].create({
                'name': packaging_id.name,
                'product_id': self.product_id.id,
                'package_type_id': packaging_id.package_type_id.id,
                'route_ids': packaging_id.route_ids,
                'qty': packaging_id.qty,
                'product_uom_id': packaging_id.product_uom_id,
                'purchase': packaging_id.purchase,
                'sales': packaging_id.sales,
                'barcode': packaging_id.barcode,
                'company_id': packaging_id.company_id.id,
            })

        for rule in self.rearrangement_rules:
            self.env['stock.warehouse.orderpoint'].create({
                'product_id': self.product_id.id,
                'warehouse_id': rule.warehouse_id.id,
                'location_id': rule.location_id.id,
                'route_id': rule.route_id.id,
                'qty_multiple': rule.qty_multiple,
                'trigger': 'manual',
                'origin_of_creation': self.picking_id.id if rule.location_id.complete_name.lower() == 'clh/existencias/u05/pasillo 01/sin regla abastecer u05' and rule.route_id.name.lower() == 'yumbo: abastecer u05' else False
            })
        if self.create_replenishment_rule:
            for route in self.env['stock.route'].search([]):
                if route.name and route.name.lower() == 'yumbo: abastecer u05':
                    self.product_id.route_ids += route
        self.stock_move_id.product_criteria_update_finished = True


class TemporalProductPackaging(models.TransientModel):
    _name = "temporal.product.packaging"

    id_origin = fields.Integer(string="Id origen")
    name = fields.Char(string="Embalaje")
    product_id = fields.Many2one("product.product", "Producto")
    product_uom_id = fields.Many2one("uom.uom")
    package_type_id = fields.Many2one('stock.package.type', 'Tipo de paquete')
    qty = fields.Float(string="Cantidad incluida")
    barcode = fields.Char(string="Código de barras")
    route_ids = fields.Many2many('stock.route', 'Rutas')
    purchase = fields.Boolean(default=False)
    sales = fields.Boolean(default=False)
    company_id = fields.Many2one('res.company', string="Empresa", default=lambda self: self.env.company)
    product_criteria_update = fields.Many2one("product.criteria.update")


class TemporalStockWarehouseOrderpoint(models.TransientModel):
    _name = "temporal.stock.warehouse.orderpoint"
    criteria = fields.Many2one("product.criteria.update")
    product_id = fields.Many2one('product.product', string="Producto")
    location_id = fields.Many2one('stock.location', 'Ubicación', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Almacen', required=True)
    route_id = fields.Many2one('stock.route', 'Ruta', required=True)
    product_min_qty = fields.Float(string="Cantidad mínima")
    product_max_qty = fields.Float(string="Cantidad mínima")
    qty_multiple = fields.Float(string="Cantidad múltiple")
    company_id = fields.Many2one('res.company', string="Empresa", default=lambda self: self.env.company)

class UserCriteriaUpdate(models.Model):
    _name = "user.criteria.update"

    user_id = fields.Many2one('res.users', "Encargado")