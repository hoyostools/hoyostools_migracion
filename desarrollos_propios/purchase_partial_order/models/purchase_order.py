from odoo import models, fields, api
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    has_selected_products = fields.Boolean(compute="_compute_has_selected_products", store=True)
    partition_origin_names = fields.Char(
        string='Documentos de orígenes partición',
        help='Nombres de las órdenes de las cuales se originó esta orden.'
    )
            
    @api.depends('order_line.selected_for_partial')
    def _compute_has_selected_products(self):
        """Verifica si hay productos seleccionados para partir"""
        for order in self:
            order.has_selected_products = any(order.order_line.mapped('selected_for_partial'))

    def action_create_partial_order(self):
        """Muestra el wizard para seleccionar entre una nueva orden o una existente."""

        for order in self:
            if not order.order_line.filtered('selected_for_partial'):
                raise UserError("Debe seleccionar al menos un producto para crear una orden parcial.")

        return {
            'name': 'Crear Orden Parcial',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.partial.order.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_purchase_id': self.id}
        }

    def action_update_split_qty(self):
        """Valida las cantidades a partir antes de dividir la orden"""
        for order in self:
            for line in order.order_line.filtered(lambda l: l.selected_for_partial):
                if line.to_split_qty <= 0:
                    raise UserError(f"La cantidad a partir en {line.product_id.display_name} debe ser mayor a 0.")
                if line.to_split_qty > line.product_qty:
                    raise UserError(f"La cantidad a partir en {line.product_id.display_name} no puede ser mayor a la cantidad original.")

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    selected_for_partial = fields.Boolean(string="Seleccion", default=False)
    to_split_qty = fields.Float(string="A Partir", help="Cantidad a mover a la nueva orden de compra o existente.")

    @api.constrains('to_split_qty')
    def _check_to_split_qty(self):
        """Evita valores negativos o mayores a la cantidad original"""
        for line in self:
            if line.to_split_qty < 0:
                raise UserError("La cantidad a partir no puede ser negativa.")
            if line.to_split_qty > line.product_qty:
                raise UserError("La cantidad a partir no puede ser mayor que la cantidad a comprar.")

