from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    audit_pick_location = fields.Boolean(string="Ubicación de auditoria del PICK")
    audit_pack_location = fields.Boolean(string="Ubicación de auditoria del PACK")