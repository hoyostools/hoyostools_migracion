from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    valor_a = fields.Float(string='Cantidad máxima para descuento:', default=False)
    valor_b = fields.Float(string='Cantidad minima para descuento:', default=False)
    descuento_rango = fields.Integer(string='Descuento en rango:', default=False)
    descuento_mayor = fields.Integer(string='Descuento supera rango:', default=False)
    applicable_sale_order = fields.Boolean(string="Venta")
    applicable_web = fields.Boolean(string="Sitio Web")




