from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    approved_for_processing = fields.Boolean(string="Aprobada para procesar", default=False)