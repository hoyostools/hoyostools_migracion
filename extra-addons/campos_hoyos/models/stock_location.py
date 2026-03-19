from odoo import models, fields


class StockLocation(models.Model):
    _inherit = "stock.location"

    responsible_location = fields.Many2one("res.users", string="Responsable locación")
    revisor_location = fields.Many2one("res.users", string="Revisor locación")