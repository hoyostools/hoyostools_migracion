from odoo import models, fields, api

class PurchaseLogbook(models.Model):
    _name = 'purchase.logbook'
    _description = 'Bitácora de Compras'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'numero_factura'

    create_date = fields.Datetime(string="Fecha de Recibo", readonly=True)
    partner_id = fields.Many2one('res.partner', string='Proveedor', required=True, tracking=True)
    numero_factura = fields.Char(string='Número de Factura', required=True, tracking=True)
    items = fields.Integer(string='Items', required=True, tracking=True)
    valor_factura = fields.Float(string='Valor de Factura', required=True, tracking=True)
    encargado_proveedor_id = fields.Many2one(
        'res.users',
        string='Encargado del Proveedor',
        related="partner_id.buyer_id",
        store=True,
        readonly=True,
        tracking=True
    )
    novedad = fields.Many2many('purchase.logbook.novedad', string='Novedades', tracking=True)
    resuelto_bodega = fields.Boolean(string='Resuelto Bodega', tracking=True)
    resuelto_compras = fields.Boolean(string='Resuelto Compras', tracking=True)
    purchase_order_ids = fields.Many2many('purchase.order', string='Órdenes de Compra', tracking=True)
    observacion = fields.Text(string='Observación')

    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('sobrantes', 'Sobrantes por solucionar'),
        ('sin_orden', 'Sin Orden de Compra'),
        ('aprobada', 'Aprobada'),
        ('ingresada', 'Ingresada'),
        ('ubicada', 'Ubicada'),
        ('cancelada', 'Cancelada'),
    ], string='Estado', default='pendiente', tracking=True)
    
    create_uid = fields.Many2one('res.users', string="Creado por", readonly=True)

    cant_pacas = fields.Integer(string='Cantidad de Pacas', required=True, tracking=True)
    transportadora_id = fields.Many2one(
        'purchase.logbook.transportadora',
        string='Transportadora',
        tracking=True
    )

    total_a_pagar = fields.Monetary(
        string="Total a Pagar",
        compute="_compute_total_a_pagar",
        store=True,
        currency_field="currency_id",
        tracking=True,
    )

    currency_id = fields.Many2one(
        'res.currency',
        string="Moneda",
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )
    
    # Campos de fecha/hora por estado
    fecha_sin_orden = fields.Datetime(string="Fecha Sin Orden de Compra", readonly=True, tracking=True)
    fecha_aprobada = fields.Datetime(string="Fecha Aprobada", readonly=True, tracking=True)
    fecha_ingresada = fields.Datetime(string="Fecha Ingresada", readonly=True, tracking=True)
    fecha_ubicada = fields.Datetime(string="Fecha Ubicada", readonly=True, tracking=True)
    fecha_sobrantes = fields.Datetime(string="Fecha Sobrantes por Solucionar", readonly=True, tracking=True)
    fecha_cancelada = fields.Datetime(string="Fecha Cancelada", readonly=True, tracking=True)

    usuario_sin_orden = fields.Many2one('res.users', string="Usuario Sin Orden", readonly=True)
    usuario_aprobada = fields.Many2one('res.users', string="Usuario Aprobada", readonly=True)
    usuario_ingresada = fields.Many2one('res.users', string="Usuario Ingresada", readonly=True)
    usuario_ubicada = fields.Many2one('res.users', string="Usuario Ubicada", readonly=True)
    usuario_sobrantes = fields.Many2one('res.users', string="Usuario Sobrantes", readonly=True)
    usuario_cancelada = fields.Many2one('res.users', string="Usuario Cancelada", readonly=True)
    
    # Sobrescribir write para registrar fecha/hora
    def write(self, vals):
        vals = dict(vals)

        if 'estado' in vals:
            now = fields.Datetime.now()
            user_id = self.env.user.id

            for record in self:
                if record.estado != vals['estado']:
                    
                    if vals['estado'] == 'sobrantes':
                        vals.update({
                            'fecha_sobrantes': now,
                            'usuario_sobrantes': user_id,
                        })
                        
                        
                    elif vals['estado'] == 'sin_orden':
                        vals.update({
                            'fecha_sin_orden': now,
                            'usuario_sin_orden': user_id,
                        })

                    elif vals['estado'] == 'aprobada':
                        vals.update({
                            'fecha_aprobada': now,
                            'usuario_aprobada': user_id,
                        })

                    elif vals['estado'] == 'ingresada':
                        vals.update({
                            'fecha_ingresada': now,
                            'usuario_ingresada': user_id,
                        })

                    elif vals['estado'] == 'ubicada':
                        vals.update({
                            'fecha_ubicada': now,
                            'usuario_ubicada': user_id,
                        })

                    elif vals['estado'] == 'cancelada':
                        vals.update({
                            'fecha_cancelada': now,
                            'usuario_cancelada': user_id,
                        })

        return super().write(vals)
    
    @api.depends('purchase_order_ids.amount_total')
    def _compute_total_a_pagar(self):
        for record in self:
            total = 0.0
            for po in record.purchase_order_ids:
                total += po.amount_total
            record.total_a_pagar = total

class PurchaseLogbookEncargado(models.Model):
    _name = 'purchase.logbook.encargado'
    _description = 'Encargado del Proveedor'

    name = fields.Char(string="Nombre y Apellido", required=True)
    phone = fields.Char(string="Teléfono")
    email = fields.Char(string="Email")


class PurchaseLogbookTransportadora(models.Model):
    _name = 'purchase.logbook.transportadora'
    _description = 'Transportadora'

    name = fields.Char(string="Nombre", required=True)
    
class PurchaseLogbookNovedad(models.Model):
    _name = 'purchase.logbook.novedad'
    _description = 'Novedad'

    name = fields.Char(string="Descripción", required=True)