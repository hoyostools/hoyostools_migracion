from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    valor_a = fields.Float(string='Hasta (Unidades)', default=False)
    valor_b = fields.Float(string='De (Unidades)', default=False)
    descuento_rango = fields.Integer(string='Obtienes % Descuento', default=False)
    descuento_mayor = fields.Integer(string='Si es Mayor Obtienes % Descuento', default=False)
    applicable_sale_order = fields.Boolean(string="Aplicable a Ventas")
    applicable_web = fields.Boolean(string="Aplicable en Web")




