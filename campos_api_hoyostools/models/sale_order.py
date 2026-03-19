from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    notas_logisticas = fields.Char(string="Notas Logisticas")