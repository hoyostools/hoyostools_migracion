from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _order = 'prioridad_real desc'

    prioridad = fields.Integer(string="Ordenes Afectadas", readonly=False, index=True)
    prioridad_real = fields.Integer(string="Ordenes Afectadas")
    desface = fields.Boolean(default=False)
    valor_orden = fields.Float(string='Valor Orden', store=True, readonly=False, index=True)
    cantidad_items = fields.Integer(string='Cantidad de Items', store=True, readonly=False, index=True)
    metodo_envio = fields.Many2many('delivery.carrier', string="Método de envío", store=True, readonly=False,
                                    index=True)

    def actualizar_datos_orden_venta(self):
        sale_orders = self.env['sale.order'].search([('name', 'in', self.mapped('origin'))])
        sale_order_map = {so.name: so for so in sale_orders}

        for picking in self:
            sale_order = sale_order_map.get(picking.origin)
            picking.metodo_envio = sale_order.carrier_id if sale_order else False
            picking.valor_orden = sale_order.amount_total if sale_order else 0.0
            picking.cantidad_items = len(picking.move_ids_without_package)

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in ['move_ids_without_package', 'origin']):
            self.actualizar_datos_orden_venta()
        return res

    @api.model
    def create(self, vals):
        picking = super().create(vals)
        try:
            picking.actualizar_datos_orden_venta()
        except:
            pass
        return picking

    def compute_ordenes(self):
        if not self:
            return

        self.env.cr.execute("""
                SELECT sp.id, COUNT(so.id) AS total
                FROM stock_picking sp
                JOIN stock_move sm ON sm.picking_id = sp.id
                JOIN product_product pp ON pp.id = sm.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                JOIN sale_order_line sol ON sol.product_id = pp.id
                JOIN sale_order so ON so.id = sol.order_id AND so.state = 'sale' AND (so.proceso_disponibilidad = 'true' or so.problema = 'true') and so.procesada = 'false'
                GROUP BY sp.id
            """)
        data = dict(self.env.cr.fetchall())
        for record in self:
            record.prioridad = data.get(record.id, 0)
            record.prioridad_real = data.get(record.id, 0)

    def button_validate(self):
        retorno = super(StockPicking, self).button_validate()
        for record in self:
            if retorno:
                if 'PACK' in record.name:
                    zonas = self.env['wave.zonas'].search([('orden', '=', record.sale_id.id)])
                    for zona in zonas:
                        zona.ocupado = False
                        zona.orden = False
        return retorno

    def obtener_horas_ordenes_hoy(self, usuario, fecha_fin, tipo):
        if fecha_fin:
            # Obtener las órdenes para hoy
            date_format = '%Y/%m/%d %H:%M'
            fecha_inicio = datetime.strptime(fecha_fin.replace('-', '/') + ' 00:00', date_format)
            fecha_fin = fecha_inicio.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            fecha_inicio = fields.Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            fecha_fin = fields.Datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)

        if tipo == 'picking':
            ordenes = self.env['stock.picking'].search(
                [('scheduled_date', '>=', fecha_inicio),
                 ('scheduled_date', '<=', fecha_fin),
                 ('user_id', '=', usuario)]
            )
        else:
            ordenes = self.env['sale.order'].search(
                [('date_order', '>=', fecha_inicio), ('date_order', '<=', fecha_fin),
                 ('picking_ids', 'in', self.env['stock.picking'].search(
                     [('user_id', '=', usuario)]).ids)]).picking_ids.batch_id.filtered(
                lambda b: b.user_id.id == usuario)

        if not ordenes:
            return None, None

        # Obtener la hora de la primer orden de hoy
        try:
            primera_orden = ordenes.sorted('scheduled_date')[0].date_done
            hora_primera_orden = primera_orden.time() if primera_orden else 'Indefinido'

            # Obtener la hora de la última orden de hoy
            ultima_orden = ordenes.sorted('scheduled_date')[-1].date_done
            hora_ultima_orden = ultima_orden.time() if ultima_orden else 'Indefinido'
        except:
            hora_primera_orden = 'Indefinido'
            hora_ultima_orden = 'Indefinido'

        return hora_primera_orden, hora_ultima_orden

    def calcular_cumplimiento(self, usuario):

        ordenes = 0
        cumplimiento = 0
        fecha_inicio = False
        fecha_fin = False
        if len(usuario) > 1:
            fecha_fin = usuario[2]
            fecha_inicio = usuario[1]
            usuario = [usuario[0]]

        motacarguistas = self.env['sale.montacargas'].browse(usuario)
        pickings = self.env['stock.picking'].search([('user_id', 'in', usuario)])
        pickings_hechos = self.env['stock.picking'].search([('state', '=', 'done'),('user_id', 'in', usuario)])
        pickings_en_proceso = self.env['stock.picking'].search([('state', 'not in', ['done', 'draft']),('user_id', 'in', usuario)])
        ordenes = self.env['stock.picking.batch'].search([('user_id', 'in', usuario),('picking_id', 'in', pickings)])
        ordenes_hechas = self.env['stock.picking.batch'].search([('user_id', 'in', usuario),('state', '=', 'done'),('picking_id', 'in', pickings)])
        ordenes_en_proceso = self.env['stock.picking.batch'].search([('user_id', 'in', usuario),('state', 'not in', ['done', 'draft']),('picking_id', 'in', pickings)])

        if motacarguistas:
            funcion = motacarguistas.funcion
            usuario = motacarguistas.user_id.id
            if 'pasillo' in funcion:
                if fecha_fin and fecha_inicio:
                    ordenes = self.env['sale.order'].search(
                        [('date_order', '>=', fecha_inicio), ('date_order', '<=', fecha_fin),
                         ('picking_ids', 'in', pickings.ids)]).picking_ids.batch_id.filtered(
                        lambda b: b.user_id.id == usuario)
                hora_inicio, hora_fin = self.obtener_horas_ordenes_hoy(usuario, fecha_fin, 'sale')
                productos = len(ordenes.picking_ids.move_ids)
                valor = sum(ordenes.picking_ids.sale_id.mapped(
                    'amount_untaxed'))
                procesadas = len(ordenes_hechas)
                en_proceso = len(ordenes_en_proceso)
                productos_procesadas = len(ordenes_hechas.picking_ids.move_ids)
                productos_en_proceso = len(
                    ordenes_en_proceso.picking_ids.move_ids)
                valor_procesadas = sum(
                    ordenes_hechas.picking_ids.sale_id.mapped('amount_untaxed'))
                valor_en_proceso = sum(
                    ordenes_en_proceso.picking_ids.sale_id.mapped(
                        'amount_untaxed'))
            elif 'piso' in funcion:
                if fecha_fin and fecha_fin:
                    ordenes = self.env['sale.order'].search(
                        [('date_order', '>=', fecha_inicio), ('date_order', '<=', fecha_fin),
                         ('picking_ids', 'in', self.env['stock.picking'].search(
                             [('user_id', '=', usuario)]).ids)]).picking_ids.batch_id.filtered(
                        lambda b: b.user_id.id == usuario)
                hora_inicio, hora_fin = self.obtener_horas_ordenes_hoy(usuario, fecha_fin, 'sale')
                productos = len(ordenes.picking_ids.move_ids)
                valor = sum(ordenes.picking_ids.sale_id.mapped('amount_untaxed'))
                procesadas = len(ordenes_hechas)
                en_proceso = len(ordenes_en_proceso)
                productos_procesadas = len(ordenes_hechas.picking_ids.product_id)
                productos_en_proceso = len(
                    ordenes_en_proceso.picking_ids.product_id)
                valor_procesadas = sum(
                    ordenes_hechas.picking_ids.sale_id.mapped('amount_untaxed'))
                valor_en_proceso = sum(
                    ordenes_en_proceso.picking_ids.sale_id.mapped(
                        'amount_untaxed'))
            elif 'turbo' == funcion:
                hora_inicio, hora_fin = self.obtener_horas_ordenes_hoy(usuario, fecha_fin, 'sale')
                if fecha_fin and fecha_fin:
                    ordenes = self.env['sale.order'].search(
                        [('date_order', '>=', fecha_inicio), ('date_order', '<=', fecha_fin),
                         ('picking_ids', 'in', self.env['stock.picking'].search(
                             [('user_id', '=', usuario)]).ids)]).picking_ids.batch_id.filtered(
                        lambda b: b.user_id.id == usuario)
                productos = len(ordenes.picking_ids.batch_id.filtered(
                    lambda b: b.user_id.id == usuario).picking_ids.move_ids)
                valor = sum(ordenes.picking_ids.sale_id.mapped('amount_untaxed'))
                procesadas = len(ordenes_hechas)
                en_proceso = len(ordenes_en_proceso)
                productos_procesadas = len(ordenes_hechas.picking_ids.product_id)
                productos_en_proceso = len(
                    ordenes_en_proceso.picking_ids.product_id)
                valor_procesadas = sum(
                    ordenes_hechas.picking_ids.sale_id.mapped('amount_untaxed'))
                valor_en_proceso = sum(
                    ordenes_en_proceso.picking_ids.sale_id.mapped(
                        'amount_untaxed'))
            elif 'mkp' == funcion:
                if fecha_fin and fecha_fin:
                    ordenes = self.env['sale.order'].search(
                        [('date_order', '>=', fecha_inicio), ('date_order', '<=', fecha_fin),
                         ('picking_ids', 'in', self.env['stock.picking'].search(
                             [('user_id', '=', usuario)]).ids)]).picking_ids.batch_id.filtered(
                        lambda b: b.user_id.id == usuario)
                hora_inicio, hora_fin = self.obtener_horas_ordenes_hoy(usuario, fecha_fin, 'sale')
                productos = len(ordenes.picking_ids.move_ids)
                valor = sum(ordenes.picking_ids.sale_id.mapped('amount_untaxed'))
                procesadas = len(ordenes_hechas)
                en_proceso = len(ordenes_en_proceso)
                productos_procesadas = len(ordenes_hechas.picking_ids.move_ids)
                productos_en_proceso = len(
                    ordenes_en_proceso.picking_ids.product_id)
                valor_procesadas = sum(
                    ordenes_hechas.picking_ids.sale_id.mapped('amount_untaxed'))
                valor_en_proceso = sum(
                    ordenes_en_proceso.picking_ids.sale_id.mapped(
                        'amount_untaxed'))
            elif 'flex' == funcion:
                ordenes = pickings.batch_id.filtered(lambda b: b.user_id.id == usuario)
                if fecha_fin and fecha_fin:
                    ordenes = self.env['sale.order'].search(
                        [('date_order', '>=', fecha_inicio), ('date_order', '<=', fecha_fin),
                         ('picking_ids', 'in', pickings.ids)]).picking_ids.batch_id.filtered(
                        lambda b: b.user_id.id == usuario)
                hora_inicio, hora_fin = self.obtener_horas_ordenes_hoy(usuario, fecha_fin, 'sale')
                productos = len(ordenes.picking_ids.move_ids)
                valor = sum(ordenes.picking_ids.sale_id.mapped('amount_untaxed'))
                procesadas = len(ordenes_hechas)
                en_proceso = len(ordenes_en_proceso)
                productos_procesadas = len(ordenes_hechas.picking_ids.move_ids)
                productos_en_proceso = len(
                    ordenes_en_proceso.picking_ids.product_id)
                valor_procesadas = sum(
                    ordenes_hechas.picking_ids.sale_id.mapped('amount_untaxed'))
                valor_en_proceso = sum(
                    ordenes_en_proceso.picking_ids.sale_id.mapped(
                        'amount_untaxed'))
            else:
                if fecha_fin and fecha_fin:
                    ordenes = self.env['stock.picking'].search(
                        [('scheduled_date', '>=', fecha_inicio), ('scheduled_date', '<=', fecha_fin),
                         ('user_id', '=', usuario)])
                hora_inicio, hora_fin = self.obtener_horas_ordenes_hoy(usuario, fecha_fin, 'picking')
                productos = len(pickings.move_ids)
                valor = sum(pickings.sale_id.mapped('amount_untaxed'))
                procesadas = len(pickings_hechos)
                productos_procesadas = len(pickings_hechos.move_ids)
                en_proceso = len(pickings_en_proceso)
                productos_en_proceso = len(pickings_en_proceso.move_ids)
                valor_procesadas = sum(
                    pickings_hechos.sale_id.mapped('amount_untaxed'))
                valor_en_proceso = sum(
                    pickings_en_proceso.sale_id.mapped(
                        'amount_untaxed'))

            cumplimiento = (len(ordenes_hechas) / (len(ordenes) if ordenes else 1)) * 100

        tiempo_promedio = self.env['stock.picking'].search(
                [('user_id', '=', usuario)]).move_ids.move_line_ids.mapped('tiempo_tarea')
        tiempo_promedio = float(sum(tiempo_promedio) / (len(tiempo_promedio) if len(tiempo_promedio) else 1))
        return round(
            cumplimiento), procesadas, en_proceso, productos_procesadas, productos_en_proceso, valor_procesadas, valor_en_proceso, len(
            ordenes), productos, valor, hora_inicio, hora_fin, tiempo_promedio

    def write(self, values):
        for record in self:
            if self.env.company.controlar_desface == 'si' and  self.desface and ('state' in values or 'date_done' in values and record.user_id):
                tarea_editable = self.search([('user_id','=', record.user_id.id),('desface','=',True)],order='prioridad_real', limit=1)
                if record.id == tarea_editable.id:
                    return super(StockPicking, self).write(values)
                else:
                    raise ValidationError("Error: Solo puede editar la tarea " + tarea_editable.name)
            else:
                return super(StockPicking, self).write(values)
