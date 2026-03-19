from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    manufacturer_id = fields.Integer()
    product_manufacturer = fields.Char()
    manufacturer_pname = fields.Char()
    manufacturer_pref = fields.Char()
    manufacturer_purl = fields.Char()