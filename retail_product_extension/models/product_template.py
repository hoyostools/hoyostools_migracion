from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    retail_product_ids = fields.One2many(
        'retail.product', 'product_tmpl_id', string='Retail Configurations')
