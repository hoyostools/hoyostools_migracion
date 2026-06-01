from odoo import models, fields, api

class B4bSaleOrder(models.Model):
    _name = "b4b.sale.order"

    name = fields.Char(string='Numero Orden')
    pedido_prov_id = fields.Integer(string='Pedido Prov ID')
    partner_id = fields.Many2one('res.partner', string='Cliente Master')
    date = fields.Date(string='Fecha Pedido Prov')
    namecustomer = fields.Char(string='Cliente')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Teléfono dl Cliente')
    address = fields.Text(string='Dirección Cliente')
    city = fields.Char(string='Ciudad')
    state = fields.Char(string='Departamento')
    country = fields.Char(string='Pais')
    document = fields.Char(string='Identificacion/nit')
    servicio_logistico = fields.Boolean(string='Servicio Logistico')
    notes = fields.Text(string='Notas del Cliente')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('send', 'Send'),
        ('confirmed', 'Confirmed'), ], string='Status', default='draft')
    sale_order_line_ids = fields.One2many('b4b.sale.order.line', 'sale_order_id',
                                          string='B4B Sale Order Lines')
    sale_order_id = fields.Many2one('sale.order', string='Orden de Venta Odoo')

class B4bSaleOrderLine(models.Model):
    _name = "b4b.sale.order.line"

    sale_order_id = fields.Many2one('b4b.sale.order', string='Orden B4B')
    default_code = fields.Char(string='Código Item')
    name = fields.Char(string='Nombre Item')
    quantity = fields.Float(string='Cantidad')
    price_unit = fields.Float(string='Precio Unitario')
    porcentaje_sl = fields.Float(string='Porcentaje SL')
    total = fields.Float(string='Total', compute='calculate_total')

    @api.depends('price_unit', 'quantity')
    def calculate_total(self):
        for line in self:
            line.total = line.quantity * line.price_unit
