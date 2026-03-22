from odoo import fields, models, api


class StockQuant(models.Model):
    _inherit = "stock.quant"

    quant_price = fields.Float(string='Precio Cantidad',compute='_compute_quant_price')
    quant_price_visible = fields.Float(string='Precio Cantidad',readonly=True)

    diff_price = fields.Float(string='Precio Diferencia',compute='_compute_diff_price')
    diff_price_visible = fields.Float(string='Precio Diferencia',readonly=True)

    @api.depends('product_id.standard_price', 'quantity')
    def _compute_quant_price(self):
        for record in self:
            record.quant_price = record.product_id.standard_price * record.quantity
            record.quant_price_visible = record.quant_price

    @api.depends('product_id.standard_price', 'inventory_diff_quantity')
    def _compute_diff_price(self):
        for record in self:
            if record.inventory_quantity:
                record.diff_price = record.product_id.standard_price * record.inventory_diff_quantity
                record.diff_price_visible = record.diff_price
            else:
                record.diff_price = record.diff_price_visible = 0