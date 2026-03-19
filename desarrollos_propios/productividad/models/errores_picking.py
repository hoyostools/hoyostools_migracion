from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ErroresPicking(models.Model):
    _name = 'productividad.errores_picking'
    _description = 'Reporte de errores en picking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    

    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True, default='Nuevo')

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        domain="[('state','=','sale'),('invoice_ids','=',False)]",
        required=True,
        tracking=True
    )
    linea_error_ids = fields.One2many(
        'productividad.linea_error_picking',
        'errores_picking_id',
        string='Items reportados',
        tracking=True
    )
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado')
    ], string='Estado', default='borrador', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('productividad.errores_picking') or 'Nuevo'
        return super().create(vals)

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


class LineaErrorPicking(models.Model):
    _name = 'productividad.linea_error_picking'
    _description = 'Detalle de items con error'

    errores_picking_id = fields.Many2one('productividad.errores_picking', string='Error Picking')
    product_id = fields.Many2one('product.product', string='Producto', required=True, tracking=True)
    product_uom_qty = fields.Float(string='Cantidad', required=True, tracking=True)
    tipo_novedad = fields.Selection([
        ('faltante', 'Faltante'),
        ('sobrante', 'Sobrante'),
        ('trocado', 'Trocado')
    ], string='Novedad', required=True, tracking=True)
    responsable = fields.Many2one('res.users', string='Responsable', tracking=True)

    def _compute_responsable(self):
        """Obtiene el responsable desde el wave (batch) relacionado con el picking."""
        for rec in self:
            rec.responsable = False
            sale_order = rec.errores_picking_id.sale_order_id
            if not sale_order or not rec.product_id:
                continue

            # Buscar todos los pickings hechos relacionados a esta orden
            pickings = self.env['stock.picking'].search([
                ('origin', '=', sale_order.name),
                ('state', '=', 'done'),
                ('batch_id', '!=', False)
            ])

            for picking in pickings:
                move_lines = picking.move_ids_without_package.filtered(
                    lambda ml: ml.product_id.id == rec.product_id.id
                )
                if move_lines:
                    rec.responsable = picking.batch_id.user_id.id
                    break

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_or_qty(self):
        for rec in self:
            sale_order = rec.errores_picking_id.sale_order_id
            if not sale_order or not rec.product_id:
                continue

            # Validar que el producto esté en la orden
            line = sale_order.order_line.filtered(lambda l: l.product_id.id == rec.product_id.id)
            if not line:
                raise ValidationError("⚠️ El producto no pertenece a la orden de venta seleccionada.")

            # Validar cantidad
            if rec.product_uom_qty > line.product_uom_qty:
                raise ValidationError(
                    f"⚠️ La cantidad ingresada ({rec.product_uom_qty}) no puede ser mayor "
                    f"a la solicitada ({line.product_uom_qty}) en la orden de venta."
                )

            rec._compute_responsable()

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._compute_responsable()
        return record

    def write(self, vals):
        res = super().write(vals)
        if 'product_id' in vals or 'errores_picking_id' in vals:
            for rec in self:
                rec._compute_responsable()
        return res
