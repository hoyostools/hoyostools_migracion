from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    conexion_odoo = fields.Boolean(
        string="Conexión con Odoo",
        help="Si está activo, este cliente sincroniza facturas con Odoo remoto."
    )
