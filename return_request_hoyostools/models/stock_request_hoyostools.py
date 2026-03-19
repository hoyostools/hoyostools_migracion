from odoo import fields, models, api
from odoo.exceptions import UserError

class page_notebook_stock_request(models.Model):
    _inherit = "stock.return.request"

    package_unit = fields.Char(string='Unidad de empaque', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user.id)
    exchange_bill = fields.Char(string='Cruzar con factura')
    pick_up_on = fields.Selection([
        ('camion propio', 'Camion Propio'),
        ('transportadore', 'Transportadora'),
        ('recoge edificio', 'Recoge en edificio'),
        ('asesor', 'Asesor')
    ], string="Recoger en", required=True)

    picking_types = fields.Many2many(
        comodel_name="stock.picking.type",
        string="Operation types",
        help="Restrict operation types to search for",
        store=True,

    )

    picking_state = fields.Selection(
        selection=[("draft", "Borrador"), ("assigned", "Listo"), ("done", "Hecho")],
        string="Estado del Picking",
        compute="_compute_picking_state"
    )
    can_edit_values = fields.Boolean( compute="_compute_can_edit_")
    has_invoice = fields.Boolean(string="Tiene Nota de Crédito", default=False)

    def _compute_can_edit_(self):
        can_edit = self.env.user.has_group('__export__.res_groups_175_a69b58cd') or self.env.user.has_group('__export__.res_groups_184_cee06de6')
        for user in self:
            if can_edit == True:
                user.can_edit_values = True
            else:
                user.can_edit_values = False

    def create_credit_note(self):
        invoice = super().create_credit_note()
        for request in self:
            if invoice.invoice_line_ids.request_return_id == request:
                request.has_invoice = True

    def _update_return_request_invoice_status(self):
        """Actualiza el campo 'has_invoice' en stock.return.request"""
        # return_requests = self.env['stock.return.request'].search([])
        for request in self:
            move_ids = request.env['account.move.line'].search(
                [('request_return_id', '=', request.id)]).move_id
            request.has_invoice = bool(move_ids)

    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.can_edit_values:
                operacion_cliente = self.env['stock.picking.type'].search(
                    [('name', '=', 'Órdenes de entrega'), '|',
                     ('sequence_id', '=', 'YUMBO Secuencia de salida'),
                     ('sequence_id', '=', 'CALI Secuencia de salida')])
                record.picking_types = operacion_cliente if bool(operacion_cliente) == True else record.picking_types
        return records
    # @api.depends("picking_id")--------------------------------------+
    def _compute_picking_state(self):
        for record in self:
            record.picking_state = record.returned_picking_ids.state if record.returned_picking_ids else "draft"

    @api.onchange('return_type')
    def static_information(self):

        if self.return_type == 'customer':
            devolver_from_solicitud = self.env['stock.location'].search([('location_id', '=', 'Partners') and ('name', '=', 'Customers')])
            devolver_a_solicitud= self.env['stock.location'].search([('location_id', '=', 'DEV/Cliente') and ('name', '=', 'Transito Seleccion')])
            operacion_cliente= self.env['stock.picking.type'].search([ ('name', '=', 'Órdenes de entrega'),'|',('sequence_id', '=', 'YUMBO Secuencia de salida'),('sequence_id', '=', 'CALI Secuencia de salida')])


            self.return_to_location = devolver_a_solicitud if bool(devolver_a_solicitud) == True and len(devolver_a_solicitud) == 1 else self.return_to_location
            self.picking_types = operacion_cliente if bool(operacion_cliente) == True else self.picking_types
            self.return_from_location = devolver_from_solicitud if bool( devolver_from_solicitud) == True and len(devolver_from_solicitud) == 1 else self.return_from_location

        else:
            pass

    @api.onchange("return_type", "partner_id")
    def onchange_locations(self):
        """UI helpers to determine locations"""
        warehouse = self._default_warehouse_id()
        if self.return_type == "supplier":
            self.return_to_location = self.partner_id.property_stock_supplier
            if self.return_from_location.usage != "internal":
                self.return_from_location = warehouse.lot_stock_id.id
        # if self.return_type == "customer":
        #     self.return_from_location = self.partner_id.property_stock_customer
        #     if self.return_to_location.usage != "internal":
        #         self.return_to_location = warehouse.lot_stock_id.id
        if self.return_type == "internal":
            self.partner_id = False
            if self.return_to_location.usage != "internal":
                self.return_to_location = warehouse.lot_stock_id.id
            if self.return_from_location.usage != "internal":
                self.return_from_location = warehouse.lot_stock_id.id

    partner_address = fields.Char(store=False)

    delivery_address = fields.Many2one("res.partner", string="Dirección de entrega")


class request_line_status(models.Model):
    _inherit = "stock.return.request.line"

    product_status = fields.Selection([
        ('bad', 'Malo'),
        ('good', 'Bueno')
    ], string="Estado de producto", required=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.depends('complete_name', 'email', 'vat', 'state_id', 'country_id', 'commercial_company_name')
    @api.depends_context('show_address', 'partner_show_db_id', 'address_inline', 'show_email', 'show_vat', 'lang')
    def _compute_display_name(self):
        super(ResPartner, self)._compute_display_name()
        for partner in self:
            if partner._context.get('from_return_request'):
                partner.display_name = partner.contact_address_complete if partner.contact_address_complete else 'Sin dirección'