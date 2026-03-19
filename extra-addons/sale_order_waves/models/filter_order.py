from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import json
import pytz
class TransientViewModel(models.TransientModel):
    _name = 'filter.order'

    tipo_planeacion = fields.Selection(
        selection=lambda self: self._get_tipo_planeacion(),
        string='Tipo de Planeación',
    )

    @api.model
    def _get_tipo_planeacion(self):
        # Aquí defines las opciones dinámicas
        opciones = [
            ('automatico', 'Automático'),
            ('semiautomatico', 'Semiautomático'),
        ]

        # Ejemplo: agregar una opción basada en alguna condición
        if self.env.company.mostrar_semiautomatico == 'no':
            opciones = [('automatico', 'Automático')]

        return opciones

    almacen = fields.Many2one('stock.warehouse', string='Almacén')
    mostrar_tipo = fields.Boolean(default=False)
    fecha_orden = fields.Datetime(string="Fecha y Hora")
    fecha_orden_mayor = fields.Datetime(string="")
    fecha_entrega = fields.Datetime(string="Fecha y Hora de la Entrega")
    fecha_entrega_mayor = fields.Datetime(string="")
    metodo_envio = fields.Many2many('delivery.carrier', string="Método de Envio", )
    cliente = fields.Many2many('res.partner', string='Cliente')
    ciudad = fields.Many2many('res.city', string='Ciudad')
    items = fields.Integer(string='No. Items')
    items_mayor = fields.Integer(string='No. Items')
    total = fields.Float(string='Total')
    total_mayor = fields.Float(string='Total mayor')
    servicio_logistico = fields.Boolean(string='Servicio Logístico', default=False)
    b4b = fields.Boolean(string='B4B', default=False)
    num_ordenes = fields.Integer(string='Número de ordenes a Procesar: ', default=6)
    num_turbo = fields.Integer(string='Número de lineas para Turbo: ', default=6)
    parametro_total = fields.Selection(string='No. Items',
                                       selection=[('=', '='), ('!=', '!='), ('>', '>'), ('>=', '>='), ('<', '<'),
                                                  ('<=', '<='), ('entre', 'es entre')],
                                       default='=')
    parametro_items = fields.Selection(string='Total',
                                       selection=[('=', '='), ('!=', '!='), ('>', '>'), ('>=', '>='), ('<', '<'),
                                                  ('<=', '<='), ('entre', 'es entre')], default='=')
    parametro_fecha_orden = fields.Selection(string='',
                                       selection=[('=', '='), ('!=', '!='), ('>', '>'), ('>=', '>='), ('<', '<'),
                                                  ('<=', '<='), ('entre', 'es entre')],
                                       default='=')
    parametro_fecha_entrega = fields.Selection(string='',
                                       selection=[('=', '='), ('!=', '!='), ('>', '>'), ('>=', '>='), ('<', '<'),
                                                  ('<=', '<='), ('entre', 'es entre')], default='=')
    termino_pago = fields.Many2many('account.payment.term', string='Terminos de pago')

    @api.onchange('almacen')
    def mostrar_tipo_planeacion(self):
        for record in self:
            record.mostrar_tipo = False
            if len(self.env['wave.almacenes'].search([])) > 0:
                if record.almacen.id in self.env['wave.almacenes'].search([]).almacen.ids:
                    record.mostrar_tipo = True
                else:
                    record.tipo_planeacion = False

    def ejecutar_accion(self):
        for record in self.env['sale.montacargas']._fields['funcion'].selection:
            if len(self.env['sale.montacargas'].search([('funcion', '=', record[0]), ('activo', '=', True)])) == 0:
                raise ValidationError(
                    "Error: Falta configurar al menos un usuario activo para la función " + str(record[1]))
        ordenes = self.env['sale.order'].search(
            [('state', 'not in', ('draft', 'sent', 'cancel')), ('carrier_id.warehouse_id', '=', self.almacen.id),
             ('procesada', '=', False)]).filtered(lambda v: v.delivery_count != 0)
        pickings = ordenes.picking_ids.filtered(lambda
                                                    o: o.state != 'done' and 'Salida' not in o.location_dest_id.name)
        ordenes = pickings.sale_id
        self.almacen.tipo_planeacion = self.tipo_planeacion
        if self.fecha_orden:
            if self.parametro_fecha_orden == '=':
                ordenes = ordenes.filtered(lambda v: v.date_order == self.fecha_orden)
            if self.parametro_fecha_orden == '!=':
                ordenes = ordenes.filtered(lambda v: v.date_order != self.fecha_orden)
            if self.parametro_fecha_orden == '<=':
                ordenes = ordenes.filtered(lambda v: v.date_order <= self.fecha_orden)
            if self.parametro_fecha_orden == '<':
                ordenes = ordenes.filtered(lambda v: v.date_order < self.fecha_orden)
            if self.parametro_fecha_orden == '>=':
                ordenes = ordenes.filtered(lambda v: v.date_order >= self.fecha_orden)
            if self.parametro_fecha_orden == '>':
                ordenes = ordenes.filtered(lambda v: v.date_order > self.fecha_orden)
            if self.parametro_fecha_orden == 'entre':
                ordenes = ordenes.filtered(lambda v: v.date_order >= self.fecha_orden_mayor and v.date_order <= self.fecha_orden)
        if self.fecha_entrega:
            if self.parametro_fecha_orden == '=':
                ordenes = ordenes.filtered(lambda v: v.commitment_date == self.fecha_entrega)
            if self.parametro_fecha_orden == '!=':
                ordenes = ordenes.filtered(lambda v: v.commitment_date != self.fecha_entrega)
            if self.parametro_fecha_orden == '<=':
                ordenes = ordenes.filtered(lambda v: v.commitment_date <= self.fecha_entrega)
            if self.parametro_fecha_orden == '<':
                ordenes = ordenes.filtered(lambda v: v.commitment_date < self.fecha_entrega)
            if self.parametro_fecha_orden == '>=':
                ordenes = ordenes.filtered(lambda v: v.commitment_date >= self.fecha_entrega)
            if self.parametro_fecha_orden == '>':
                ordenes = ordenes.filtered(lambda v: v.commitment_date > self.fecha_entrega)
            if self.parametro_fecha_orden == 'entre':
                ordenes = ordenes.filtered(lambda v: v.commitment_date >= self.fecha_entrega_mayor and v.commitment_date <= self.fecha_entrega)
        if self.metodo_envio:
            ordenes = ordenes.filtered(lambda v: v.carrier_id in self.metodo_envio)
        if self.termino_pago:
            ordenes = ordenes.filtered(lambda v: v.payment_term_id in self.termino_pago)
        if self.cliente:
            ordenes = ordenes.filtered(lambda v: v.partner_id in self.cliente)
        # if self.ciudad:
        #     ordenes = ordenes.filtered(lambda v: v. self.ciudad)
        if self.items:
            if self.parametro_items == '=':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) == self.items)
            if self.parametro_items == '!=':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) != self.items)
            if self.parametro_items == '<=':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) <= self.items)
            if self.parametro_items == '<':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) < self.items)
            if self.parametro_items == '>=':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) >= self.items)
            if self.parametro_items == '>':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) > self.items)
            if self.parametro_items == 'entre':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) >= self.items_mayor and len(v.order_line) <= self.items)

        if self.total:
            if self.parametro_total == '=':
                ordenes = ordenes.filtered(lambda v: v.amont_total == self.total)
            if self.parametro_total == '!=':
                ordenes = ordenes.filtered(lambda v: v.amont_total != self.total)
            if self.parametro_total == '<':
                ordenes = ordenes.filtered(lambda v: v.amont_total < self.total)
            if self.parametro_total == '<=':
                ordenes = ordenes.filtered(lambda v: v.amont_total <= self.total)
            if self.parametro_total == '>=':
                ordenes = ordenes.filtered(lambda v: v.amont_total >= self.total)
            if self.parametro_total == '>':
                ordenes = ordenes.filtered(lambda v: v.amont_total > self.total)
            if self.parametro_total == 'entre':
                ordenes = ordenes.filtered(lambda v: v.amont_total >= self.total_mayor and self.parametro_total <= self.total)
        if self.b4b:
           ordenes = ordenes.filtered(lambda v: v.b4b == self.b4b)
        if self.servicio_logistico:
           ordenes = ordenes.filtered(lambda v: v.servicio_logistico == self.servicio_logistico)

        i = 0

        for orden in ordenes:
            orden.num_turbo = self.num_turbo
            orden.numero_items = len(orden.order_line)
            if orden.picking_ids.filtered(lambda v: 'PICK' in v.name):
                for pick in orden.picking_ids.filtered(lambda v: 'PICK' in v.name):
                    if pick.state not in ['draft', 'confirmed']:
                        orden.problema = False
        if len(ordenes.filtered(lambda v: not v.procesada and v.a_procesar)) <= self.num_ordenes:
            while i < self.num_ordenes:
                if len(ordenes.filtered(lambda v: not v.procesada and v.a_procesar)) == self.num_ordenes:
                    break
                if i > (len(ordenes) - 1):
                    break
                if not ordenes[i].problema and ordenes[i].procesada == False:
                    ordenes[i].a_procesar = True
                else:
                    ordenes[i].a_procesar = False
                    # Aumentar dinámicamente la lista y el contador de órdenes
                    self.num_ordenes = (self.num_ordenes + 1) if self.num_ordenes < len(ordenes) else self.num_ordenes
                i += 1

        # ordenes.process_availability()
        view_id = self.env.ref('sale_order_waves.view_order_logistic_tree').sudo()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Planeación Logística'),
            'res_model': 'sale.order',
            'view_mode': 'tree,kanban,form,calendar,pivot,graph,activity',
            'views': [(view_id.id, 'tree'), (False, 'form'), (False, 'kanban'), (False, 'calendar'), (False, 'pivot'),
                      (False, 'graph'), (False, 'activity')],
            'target': 'main',
            'domain': [('id', 'in', ordenes.ids)],
            'context': "{'create': False}"
        }

    def date_timezone(self, date):
        """Convierte la fecha a la zona horaria del usuario."""
        user_tz = pytz.timezone(self.env.user.tz if self.env.user.tz else 'UTC')
        new_date = pytz.utc.localize(date).astimezone(user_tz).replace(tzinfo=None)

        return new_date

    def planear(self):
        for record in self.env['sale.montacargas']._fields['funcion'].selection:
            if len(self.env['sale.montacargas'].search([('funcion', '=', record[0]), ('activo', '=', True)])) == 0:
                raise ValidationError(
                    "Error: Falta configurar al menos un usuario activo para la función " + str(record[1]))
        ordenes = self.env['sale.order'].search(
            [('state', 'not in', ('draft', 'sent', 'cancel')), ('carrier_id.warehouse_id', '=', self.almacen.id),
             ('procesada', '=', False)]).filtered(lambda v: v.delivery_count != 0)
        pickings = ordenes.picking_ids.filtered(lambda
                                                    o: o.state != 'done' and 'Salida' not in o.location_dest_id.name)
        ordenes = pickings.sale_id.sorted(key=lambda o: o.create_date)
        domain = {}

        if self.fecha_orden:
            # self.fecha_orden = self.date_timezone(self.fecha_orden)
            # self.fecha_orden_mayor = self.date_timezone(self.fecha_orden_mayor)
            if self.parametro_fecha_orden == '=':
                ordenes = ordenes.filtered(lambda v: v.date_order == self.fecha_orden)
            if self.parametro_fecha_orden == '!=':
                ordenes = ordenes.filtered(lambda v: v.date_order != self.fecha_orden)
            if self.parametro_fecha_orden == '<=':
                ordenes = ordenes.filtered(lambda v: v.date_order <= self.fecha_orden)
            if self.parametro_fecha_orden == '<':
                ordenes = ordenes.filtered(lambda v: v.date_order < self.fecha_orden)
            if self.parametro_fecha_orden == '>=':
                ordenes = ordenes.filtered(lambda v: v.date_order >= self.fecha_orden)
            if self.parametro_fecha_orden == '>':
                ordenes = ordenes.filtered(lambda v: v.date_order > self.fecha_orden)
            if self.parametro_fecha_orden == 'entre':
                ordenes = ordenes.filtered(
                    lambda v: v.date_order >= self.fecha_orden_mayor and v.date_order <= self.fecha_orden)
            domain['fecha_orden'] = str(self.fecha_orden)
            domain['fecha_orden_mayor'] = str(self.fecha_orden_mayor)
            domain['parametro_fecha_orden'] = self.parametro_fecha_orden
        if self.fecha_entrega:
            # self.fecha_entrega = self.date_timezone(self.fecha_entrega)
            # self.fecha_entrega_mayor = self.date_timezone(self.fecha_entrega_mayor)
            if self.parametro_fecha_orden == '=':
                ordenes = ordenes.filtered(lambda v: v.commitment_date == self.fecha_entrega)
            if self.parametro_fecha_orden == '!=':
                ordenes = ordenes.filtered(lambda v: v.commitment_date != self.fecha_entrega)
            if self.parametro_fecha_orden == '<=':
                ordenes = ordenes.filtered(lambda v: v.commitment_date <= self.fecha_entrega)
            if self.parametro_fecha_orden == '<':
                ordenes = ordenes.filtered(lambda v: v.commitment_date < self.fecha_entrega)
            if self.parametro_fecha_orden == '>=':
                ordenes = ordenes.filtered(lambda v: v.commitment_date >= self.fecha_entrega)
            if self.parametro_fecha_orden == '>':
                ordenes = ordenes.filtered(lambda v: v.commitment_date > self.fecha_entrega)
            if self.parametro_fecha_orden == 'entre':
                ordenes = ordenes.filtered(lambda
                                               v: v.commitment_date >= self.fecha_entrega_mayor and v.commitment_date <= self.fecha_entrega)
            domain['fecha_entrega'] = str(self.fecha_entrega)
            domain['fecha_entrega_mayor'] = str(self.fecha_entrega_mayor)
            domain['parametro_fecha_entrega'] = self.parametro_fecha_entrega
        if self.metodo_envio:
            ordenes = ordenes.filtered(lambda v: v.carrier_id in self.metodo_envio)
            domain['metodo_envio'] = [(5, 0, 0), (6, 0, self.metodo_envio.ids)]
        if self.termino_pago:
            ordenes = ordenes.filtered(lambda v: v.payment_term_id in self.termino_pago)
            domain['termino_pago'] = [(5, 0, 0), (6, 0, self.termino_pago.ids)]
        if self.cliente:
            ordenes = ordenes.filtered(lambda v: v.partner_id in self.cliente)
            domain['cliente'] = [(5, 0, 0), (6, 0, self.cliente.ids)]
        # if self.ciudad:
        #     ordenes = ordenes.filtered(lambda v: v. self.ciudad)
        if self.items:
            if self.parametro_items == '=':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) == self.items)
            if self.parametro_items == '!=':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) != self.items)
            if self.parametro_items == '<=':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) <= self.items)
            if self.parametro_items == '<':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) < self.items)
            if self.parametro_items == '>=':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) >= self.items)
            if self.parametro_items == '>':
                ordenes = ordenes.filtered(lambda v: len(v.order_line) > self.items)
            if self.parametro_items == 'entre':
                ordenes = ordenes.filtered(
                    lambda v: len(v.order_line) >= self.items_mayor and len(v.order_line) <= self.items)
            domain['items'] = self.items
            domain['parmetro_items'] = self.parametro_items
        if self.total:
            if self.parametro_total == '=':
                ordenes = ordenes.filtered(lambda v: v.amont_total == self.total)
            if self.parametro_total == '!=':
                ordenes = ordenes.filtered(lambda v: v.amont_total != self.total)
            if self.parametro_total == '<':
                ordenes = ordenes.filtered(lambda v: v.amont_total < self.total)
            if self.parametro_total == '<=':
                ordenes = ordenes.filtered(lambda v: v.amont_total <= self.total)
            if self.parametro_total == '>=':
                ordenes = ordenes.filtered(lambda v: v.amont_total >= self.total)
            if self.parametro_total == '>':
                ordenes = ordenes.filtered(lambda v: v.amont_total > self.total)
            if self.parametro_total == 'entre':
                ordenes = ordenes.filtered(
                    lambda v: v.amont_total >= self.total_mayor and self.parametro_total <= self.total)
            domain['total'] = self.total
            domain['parametro_total'] = self.parametro_total
        if self.b4b:
            ordenes = ordenes.filtered(lambda v: v.b4b)
            domain['b4b'] = self.b4b
        i = 0

        for orden in ordenes:
            orden.numero_items = len(orden.order_line)
            if orden.picking_ids.filtered(lambda v: 'PICK' in v.name):
                for pick in orden.picking_ids.filtered(lambda v: 'PICK' in v.name):
                    if pick.state not in ['draft', 'confirmed']:
                        orden.problema = False
        while i < len(ordenes):
            if i > (len(ordenes) - 1):
                break
            if not ordenes[i].problema and ordenes[i].procesada == False:
                ordenes[i].a_procesar = True
            else:
                ordenes[i].a_procesar = False
            i += 1
        domain['almacen'] = self.almacen.id
        domain['tipo_planeacion'] = self.tipo_planeacion
        self.almacen.tipo_planeacion = self.tipo_planeacion
        domain['num_turbo'] = self.num_turbo
        domain['num_ordenes'] = self.num_ordenes
        dominio = json.dumps(domain)
        if dominio == self.almacen.dominio and self.env.user.id != 1:
            raise ValidationError("Error: Ya se encuentra ejecutando un proceso de planeación automatica con esta configuración")
        self.almacen.dominio = dominio
        if not self.almacen.piso:
            ordenes.filtered(lambda o: o.a_procesar == True).process_availability()
        if self.almacen.pasillo:
            ordenes.filtered(lambda o: o.a_procesar == True)[:self.num_ordenes].crear_oleadas_pasillo()
        if self.almacen.piso:
            ordenes.filtered(lambda o: o.a_procesar == True)[:self.num_ordenes].crear_oleadas_piso()
        if self.almacen.turbo and self.num_turbo > 0:
            for order in ordenes.filtered(lambda o: o.a_procesar == True)[:self.num_ordenes]:
                order.num_turbo = self.num_turbo
            ordenes.filtered(lambda o: o.a_procesar == True)[:self.num_ordenes].clh_turbo()
        if self.almacen.mkp:
            ordenes.filtered(lambda o: o.a_procesar == True)[:self.num_ordenes].clh_mkp()
        if self.almacen.flex:
            ordenes.filtered(lambda o: o.a_procesar == True)[:self.num_ordenes].clh_flex()