from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    creado_api = fields.Boolean("Creado por API")
