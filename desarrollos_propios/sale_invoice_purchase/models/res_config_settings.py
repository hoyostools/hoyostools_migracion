from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    auto_create_po_from_invoice = fields.Boolean(
        string="Crear Orden de Compra desde Factura de Venta",
        config_parameter="sale_invoice_purchase.auto_create_po_from_invoice",
        help="Si está activo, al validar una factura de cliente se generará una orden de compra en borrador."
    )