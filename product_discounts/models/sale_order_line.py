from odoo import fields, models

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    descuento_1 = fields.Float(related='product_template_id.descuento_1', string='Desc. 1', store=False)
    descuento_2 = fields.Float(related='product_template_id.descuento_2', string='Desc. 2', store=False)
    descuento_3 = fields.Float(related='product_template_id.descuento_3', string='Desc. 3', store=False)
