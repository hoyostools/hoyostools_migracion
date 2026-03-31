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

    def calcular_cumplimiento(self, usuario_data):

        if not usuario_data:
            return (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, False, False, 0)

        user_id = usuario_data[0]
        fecha_inicio = False
        fecha_fin = False

        if len(usuario_data) > 1:
            fecha_inicio = usuario_data[1]

        if len(usuario_data) > 2:
            fecha_fin = usuario_data[2]

        montacargas = self.env['sale.montacargas'].search(
            [('id', '=', user_id)],
            limit=1
        )

        if not montacargas:
            return (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, False, False, 0)

        funcion = (montacargas.funcion or '').lower()

        user_id = montacargas.user_id.id

        domain_batch = [
            ('user_id', '=', user_id)
        ]

        if fecha_inicio:
            domain_batch.append(
                ('create_date', '>=', fecha_inicio)
            )

        if fecha_fin:
            domain_batch.append(
                ('create_date', '<=', fecha_fin)
            )

        batches = self.env['stock.picking.batch'].search(domain_batch)

        pickings = batches.picking_ids

        if not pickings:
            pickings = self.env['stock.picking'].search([('user_id', '=', user_id),('date', '>=', fecha_inicio),('date', '<=', fecha_fin)])
            if not pickings:
                return (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, False, False, 0)

        ordenes_rs = pickings.sale_id

        ordenes_done = pickings.filtered(lambda p: p.state == 'done').sale_id

        ordenes_proceso = ordenes_rs - ordenes_done

        # detectar si es empaque
        es_empaque = 'empaque' in funcion

        if es_empaque:

            move_lines = pickings.move_line_ids

            productos = len(move_lines)

            productos_procesadas = len(move_lines.filtered(lambda p: p.state == 'done'))

            productos_en_proceso = productos - productos_procesadas


        else:

            moves = pickings.move_ids_without_package

            productos = len(moves)

            productos_procesadas = len(moves.filtered(lambda p: p.state == 'done'))

            productos_en_proceso = productos - productos_procesadas

        # valores
        valor = sum(
            ordenes_rs.mapped('amount_untaxed')
        )

        valor_procesadas = sum(
            ordenes_done.mapped('amount_untaxed')
        )

        valor_en_proceso = sum(
            ordenes_proceso.mapped('amount_untaxed')
        )

        procesadas = len(ordenes_done)

        en_proceso = len(ordenes_proceso)

        numero_ordenes = len(ordenes_rs)

        cumplimiento = (
                               procesadas /
                               (numero_ordenes if numero_ordenes else 1)
                       ) * 100

        hora_inicio, hora_fin = self.obtener_horas_ordenes_hoy(
            user_id,
            fecha_fin,
            'sale'
        )

        tiempos = pickings.move_line_ids.mapped(
            'tiempo_tarea'
        )

        tiempo_promedio = float(
            sum(tiempos) /
            (len(tiempos) if tiempos else 1)
        )

        return (

            round(cumplimiento),

            procesadas,
            en_proceso,

            productos_procesadas,
            productos_en_proceso,

            valor_procesadas,
            valor_en_proceso,

            numero_ordenes,
            productos,
            valor,

            hora_inicio,
            hora_fin,

            tiempo_promedio

        )

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
