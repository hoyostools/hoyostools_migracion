from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_customer = fields.Boolean(
        string="Is Customer"
    )

    is_supplier = fields.Boolean(
        string="Is Supplier"
    )