from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ErroresPacking(models.Model):
    _name = 'productividad.errores_packing'
    _description = 'Reporte de errores en packing'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Consecutivo', readonly=True, copy=False, default='Nuevo')
    sale_order_id = fields.Many2one('sale.order', string='Orden de Venta', domain="[('state','=','sale')]", required=True, tracking=True)
    linea_error_ids = fields.One2many('productividad.linea_error_packing', 'errores_packing_id', string='Items reportados', tracking=True)

    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado')
    ], string='Estado', default='borrador', tracking=True)

    def action_confirmar(self):
        for rec in self:
            rec.estado = 'confirmado'

    def write(self, vals):
        if any(rec.estado == 'confirmado' for rec in self):
            raise ValidationError("No se puede modificar un reporte confirmado.")
        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.estado == 'confirmado':
                raise ValidationError("No se puede eliminar un reporte confirmado.")
        return super().unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('productividad.errores_packing') or 'Nuevo'
        return super().create(vals)

class LineaErrorPacking(models.Model):
    _name = 'productividad.linea_error_packing'
    _description = 'Detalle de items con error en packing'

    errores_packing_id = fields.Many2one('productividad.errores_packing', string='Error Packing')
    product_id = fields.Many2one('product.product', string='Producto', required=True, tracking=True)
    product_uom_qty = fields.Float(string='Cantidad', required=True, tracking=True)
    tipo_novedad = fields.Selection([
        ('faltante', 'Faltante'),
        ('sobrante', 'Sobrante'),
        ('trocado', 'Trocado')
    ], string='Novedad', required=True, tracking=True)
    responsable = fields.Many2one('res.users', string='Responsable', tracking=True)

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_or_qty(self):
        for rec in self:
            sale_order = rec.errores_packing_id.sale_order_id
            if not sale_order or not rec.product_id:
                return

            line = sale_order.order_line.filtered(lambda l: l.product_id.id == rec.product_id.id)
            if not line:
                raise ValidationError("⚠️ El producto no pertenece a la orden de venta seleccionada.")

            if rec.product_uom_qty > line.product_uom_qty:
                raise ValidationError(
                    f"⚠️ La cantidad ingresada ({rec.product_uom_qty}) no puede ser mayor "
                    f"a la solicitada ({line.product_uom_qty}) en la orden de venta."
                )

            # Buscar responsable desde los pickings tipo Empaquetar
            pickings = self.env['stock.picking'].search([
                ('origin', '=', sale_order.name),
                ('state', '=', 'done'),
                ('picking_type_id.name', 'ilike', 'Empaquetar'),
            ])
            for picking in pickings:
                if picking.batch_id:
                    if any(m.product_id == rec.product_id for m in picking.move_ids_without_package):
                        rec.responsable = picking.batch_id.user_id.id
                        break
