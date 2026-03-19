from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    warranty_duration = fields.Float()
    warranty_return_partner = fields.Char()
    warranty_return_address = fields.Char()
    active_supplier = fields.Boolean()
    return_instructions = fields.Integer()
    return_address = fields.Char()