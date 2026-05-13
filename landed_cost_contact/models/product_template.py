from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    landed_cost_contact_ids = fields.Many2many(
        "res.partner",
        string="Contactos autorizados",
    )