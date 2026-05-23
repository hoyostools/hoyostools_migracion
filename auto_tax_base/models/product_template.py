from odoo import api, models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    no_validar_bases = fields.Boolean(string='No Validar Bases', default=False)