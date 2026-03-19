from odoo import models, fields, _, exceptions

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    campaign_id = fields.Many2one(
        "utm.campaign", string="Campaña", help="Campaña de factura origen desde el proveedor asociada a esta orden de compra."
    )
    
    