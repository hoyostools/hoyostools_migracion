from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RetailProduct(models.Model):
    _name = 'retail.product'
    _description = 'Producto Retail'
    _rec_name = 'product_tmpl_id'
    _sql_constraints = [
        ('unique_product_warehouse', 
         'unique(product_tmpl_id, warehouse_id)',
         'El producto ya está configurado para este almacén.')
    ]

    product_tmpl_id = fields.Many2one(
        'product.template', string='Producto', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', string='Variante del Producto', required=False)
    store_id = fields.Char(string='ID Tienda')
    barcode = fields.Char(string='Código de Barras')
    warehouse_id = fields.Many2one('stock.warehouse', string='Almacén', required=True)

    @api.model
    def create(self, vals):
        """Si el producto tiene variante, llenamos la plantilla automáticamente."""
        if vals.get('product_id') and not vals.get('product_tmpl_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            vals['product_tmpl_id'] = product.product_tmpl_id.id
        return super().create(vals)

    @api.constrains('product_tmpl_id', 'warehouse_id')
    def _check_unique_product_warehouse(self):
        for record in self:
            duplicates = self.search([
                ('id', '!=', record.id),
                ('product_tmpl_id', '=', record.product_tmpl_id.id),
                ('warehouse_id', '=', record.warehouse_id.id)
            ])
            if duplicates:
                raise ValidationError(
                    f"El producto '{record.product_tmpl_id.display_name}' ya está configurado en el almacén '{record.warehouse_id.display_name}'."
                )
