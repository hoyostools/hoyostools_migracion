from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    contado_por = fields.Many2one(
        'res.users',
        string='Contado por',
        readonly=True
    )
    
    product_default_code = fields.Char(
        string='Referencia Interna',
        related='product_id.default_code',
        store=True,
        readonly=True
    )

    @api.model
    def create(self, vals):
        if 'inventory_quantity' in vals:
            vals['contado_por'] = self.env.uid
        return super().create(vals)

    def write(self, vals):
        if 'inventory_quantity' in vals:
            vals['contado_por'] = self.env.uid
        return super().write(vals)

    @api.model
    def _get_inventory_fields_write(self):
        res = super()._get_inventory_fields_write()
        res.append('contado_por')
        return res

