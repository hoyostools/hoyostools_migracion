from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = "product.template"

    manufacturer_id = fields.Many2one(
        "res.partner",
        string="Fabricante",
        domain=[
            ("type", "=", "contact"),
            ("is_supplier", "=", True),
        ]
    )

    manufacturer_pname = fields.Char(
        string="Nombre de producto del fabricante"
    )

    manufacturer_pref = fields.Char(
        string="Código de producto del fabricante"
    )

    manufacturer_purl = fields.Char(
        string="URL de producto del fabricante"
    )