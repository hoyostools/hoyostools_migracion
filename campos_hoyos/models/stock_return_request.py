from odoo import fields, models, api
from odoo.exceptions import UserError

class StockReturnRequestLine(models.Model):
    _inherit = "stock.return.request.line"

    @api.onchange('product_id')
    def validation_warranty_offered_by_supplier(self):
        for line in self:
            if line.product_id.warranty_offered_by_supplier and line.request_id.return_type == 'customer':
                raise UserError("El producto tiene garantía ofrecida por el proveedor")

