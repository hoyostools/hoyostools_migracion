from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    address_complete = fields.Char(related='partner_id.contact_address_complete')
    carrier_id_name = fields.Char(related='carrier_id.name')