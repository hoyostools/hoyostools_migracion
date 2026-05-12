from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # address_complete = fields.Char(related='partner_id.contact_address_complete')
    # carrier_id_name = fields.Char(related='carrier_id.name')
    packaging_order_observation = fields.Text(string='Totalidad del empaque de la orden', related='sale_id.packaging_order_observation', store=True, readonly=False,)