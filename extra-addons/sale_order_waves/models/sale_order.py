from odoo import fields, models, api, _

class SaleOrderWave(models.Model):
    _inherit = 'sale.order'

    servicio_logistico = fields.Boolean(string='Servicio Logístico', default=False)
    num_items = fields.Many2one('sale.order.line', string="Items")
    numero_items = fields.Integer(string="Items")
    ciudad_destino = fields.Many2many('res.city', string="Ciudad Destino")
    problema = fields.Boolean(string='Problema', default=False)
    b4b = fields.Boolean(string='B4B', default=False)
    tipo_planeacion = fields.Selection(string='Tipo de Planeación',
                                       selection=[('auntomatico', 'Automático'), ('semiautomatico', 'Semiautomático')])
    almacen = fields.Many2one('stock.warehouse', string='Almacén')
    proceso_disponibilidad = fields.Boolean(default=False)
    a_procesar = fields.Boolean(default=False)
    procesada = fields.Boolean(default=False)
    num_turbo = fields.Integer()

    @api.depends('picking_ids')
    def calculate_problem(self):
        view_id = self.env.ref('sale_order_waves.view_filter_logistic_form').sudo()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Planeación Logística'),
            'res_model': 'filter.order',
            'view_mode': 'form',
            'views': [(view_id.id, 'form')],
            'target': 'new'
        }

    def process_availability(self):
        ordersnotready = []

        # Cache de búsquedas comunes
        warehouse_location = self.env['stock.location'].search([('funcion', '=', 'bodegaje')]).filtered(lambda b: 'CLH/Existencias' in b.complete_name)[0]
        warehouse_location2 = self.env['stock.location'].search([('funcion', '=', 'bodegaje')]).filtered(lambda b: 'CLH/Existencias' in b.complete_name)[0]
        picking_type_internal = self.env['stock.picking.type'].search([('barcode', '=', 'CLH-INTERNAL')], limit=1)
        montacargas_users = self.env['sale.montacargas'].search(
            [("activo", "=", True), ("funcion", "=", "montacargas")]
        ).mapped('user_id.id')


        # Determinar órdenes no listas
        for reg in self:
            if reg.state in ['sale', 'done'] and not reg.problema and not reg.proceso_disponibilidad:
                is_ready = all(
                    'PICK' not in pick.name or pick.state == 'assigned'
                    for pick in reg.picking_ids
                )
                if not is_ready:
                    ordersnotready.append(reg)
                reg.proceso_disponibilidad = True

        if not ordersnotready:
            return True

        product_sums = {}
        for order in ordersnotready:
            order["problema"] = True
            order["a_procesar"] = False
            for pick in order.picking_ids:
                if "PICK" in pick.name and pick.state != 'cancel':
                    for line in pick.move_ids_without_package:
                        if line.product_uom_qty > line.quantity:
                            demanda = line.product_uom_qty
                            disponible = self.env['stock.quant']._get_quants_by_products_locations(line.product_id,warehouse_location)
                            if disponible:
                                disponible = disponible[line.product_id.id].filtered(lambda b: b.quantity > line.product_uom_qty and b.location_id.funcion == 'bodegaje')
                                if disponible:
                                    warehouse_location2 = disponible[0].location_id
                            location_id = line.location_id.id

                            # Buscar punto de pedido para determinar ubicación
                            loc_orderpoints = self.env['stock.warehouse.orderpoint'].search([
                                ("product_id", "=", line.product_id.id),
                                ("location_id.complete_name", "ilike", "CLH/Existencias/U02/U05")
                            ], limit=1)

                            if loc_orderpoints:
                                location_id = loc_orderpoints.location_id.id

                            # Acumular demanda por producto y ubicación
                            key = (line.product_id.id, location_id)
                            product_sums[key] = product_sums.get(key, 0) + demanda

        pickings = []
        for (product_id, product_location), quantity in product_sums.items():
            disponible = self.env['stock.quant']._get_quants_by_products_locations(
                self.env['product.product'].search([('id', '=', product_id)]), warehouse_location)
            if disponible:
                disponible = disponible[product_id].filtered(
                    lambda b: b.quantity > quantity and b.location_id.funcion == 'bodegaje')
                if disponible:
                    warehouse_location2 = disponible[0].location_id
            existing_move = self.env['stock.move'].search([
                ('location_id', '=', warehouse_location2.id),
                ('location_dest_id', '=', product_location),
                ('product_id', '=', product_id),
                ('state', 'not in', ['done', 'cancel', 'draft'])
            ], limit=1)

            if existing_move:
                existing_move.product_uom_qty += quantity
            else:
                new_picking = self.env['stock.picking'].create({
                    "picking_type_id": picking_type_internal.id,
                    "location_id": warehouse_location2.id,
                    "location_dest_id": product_location,
                    'desface': True
                })
                self.env['stock.move'].create({
                    "location_id": warehouse_location2.id,
                    "location_dest_id": product_location,
                    'picking_id': new_picking.id,
                    'product_id': product_id,
                    'product_uom_qty': quantity,
                    'name': "",
                })
                pickings.append(new_picking.id)

        if pickings:
            picking = self.env['stock.picking'].browse(pickings)
            picking.action_confirm()
            picking.action_assign()
            picking.filtered(lambda b: b.state == 'confirmed').unlink()


        if pickings and montacargas_users:
            cantidad_montacargas = len(montacargas_users)
            if cantidad_montacargas > 0:
                for index, picking in enumerate(picking):
                    try:
                        picking.user_id = montacargas_users[index%cantidad_montacargas]
                    except:
                        pass

        return True

    def action_draft(self):
        for record in self:
            zonas = self.env['wave.zonas'].search([('orden', '=', record.id)])
            for zona in zonas:
                zona.ocupado = False
                zona.orden = False
        retorno = super(SaleOrderWave, self).action_draft()
        return retorno

    def action_cancel(self):
        for record in self:
            record.proceso_disponibilidad = False
        retorno = super(SaleOrderWave, self).action_cancel()
        return retorno

    def crear_oleadas_pasillo(self):
        def addtowave(pas, zona, ordenes):
            wave = False
            if len(zona) > 0:
                orden_actual = self.env['sale.order'].search([('name', '=', zona[0].picking_id.origin)])
                pas["asignaciones"] += 1
                wave = self.env['stock.picking.batch'].search([('state','=','in_progress'),('user_id' , '=' , pas.user_id.id),('name','ilike','CLH'),('ordenes','!=',False)], limit=1).filtered(lambda o: orden_actual in o.ordenes)
                if not wave or orden_actual not in wave.ordenes:
                    wave = self.env["stock.picking.batch"].create({
                        'picking_type_id': 3,
                        'is_wave': True,
                        'user_id': pas.user_id.id,
                        'ordenes' : ordenes.ids,
                    })
                    wave["name"] = wave.name + "-CLH"
                for line in zona:
                    # log("Wave " + wave.name + " picking " + str(line.picking_id.name) + " tipo " + str(line.picking_type_id) + " Zona " + line.location_id.complete_name + " Producto " + line.product_id.default_code, level='info')
                    try:
                        line._add_to_wave(wave)
                    except:
                        wave1 = self.env["stock.picking.batch"].create({
                            'picking_type_id': 3,
                            'is_wave': True,
                            'user_id': pas.user_id.id,
                            'ordenes': ordenes.ids,
                        })
                        line._add_to_wave(wave1)
                        wave1["name"] = wave1.name + "-CLH"

            if wave:
                wave.actualizar_campos_ordenes()
                return wave
            else:
                return False

        ordersready = self.env['sale.order']
        ordersnotready = self.env['sale.order']
        # usuarios para 12 pasillos y 2 pisos
        pas01 = None
        pas02 = None
        pas03 = None
        pas04 = None
        pas05 = None
        pas06 = None
        pas07 = None
        pas08 = None
        pas09 = None
        pas10 = None
        pas11 = None
        pas12 = None

        # estructuras para las lineas de movimiento para cada pasillo
        pasillo01r = []
        pasillo02r = []
        pasillo03r = []
        pasillo04r = []
        pasillo05r = []
        pasillo06r = []
        pasillo07r = []
        pasillo08r = []
        pasillo09r = []
        pasillo10r = []
        pasillo11r = []
        pasillo12r = []

        zonas = []

        for reg in self:
            if reg.state in ['sale', 'done'] and not reg.problema:
                isready = True
                for pick in reg.picking_ids:
                    if 'PICK' in pick.name and pick.state != 'assigned':
                        isready = False
                if isready == True:
                    ordersready += reg
                else:
                    ordersnotready += reg

                if len(ordersready) == 10:
                    break

        if len(ordersready) > 0 or len(ordersnotready) > 0:

            empleadosMontacargas = self.env["sale.montacargas"].search(
                [("activo", "=", True), ("funcion", "=", "montacargas")])
            waveorders = 0
            contadororders = 0
            numorders = len(ordersready)
            if numorders > 0:
                for order in ordersready:
                    oleada = False
                    zonas = self.env['wave.zonas'].search([('metodo_de_envio', '=', order.carrier_id.id),('ocupado','=',False)])
                    if len(order.order_line) >= 7  and len(zonas) > 0:
                        seproceso = False
                        pickaddname = ""
                        if len(zonas) > 0:
                            orderzone = zonas[0]
                            pickaddname = orderzone.name
                            zonereg = order.picking_ids.filtered(lambda b: 'PICK' in b.name).location_dest_id
                            contadororders += 1
                            waveorders += 1

                            for pick in order.picking_ids:
                                if "PICK" in pick.name and pick.picking_type_id.id == 3:
                                    for line in pick.move_line_ids:
                                        if zonereg:
                                            line["location_dest_id"] = zonereg.id
                                        if line.location_id.funcion == 'pasillo01' and order.carrier_id.tipo in [
                                            'ruta', 'horas', 'despacho']:
                                            pasillo01r.append(line)
                                        elif line.location_id.funcion == 'pasillo02' and order.carrier_id.tipo in [
                                            'ruta', 'horas', 'despacho']:
                                            pasillo02r.append(line)
                                        elif line.location_id.funcion == 'pasillo03' and order.carrier_id.tipo in [
                                            'ruta', 'horas', 'despacho']:
                                            pasillo03r.append(line)
                                        elif line.location_id.funcion == 'pasillo04' and order.carrier_id.tipo in [
                                            'ruta', 'horas', 'despacho']:
                                            pasillo04r.append(line)
                                        elif line.location_id.funcion == 'pasillo05' and order.carrier_id.tipo in [
                                            'ruta', 'horas', 'despacho']:
                                            pasillo05r.append(line)
                                        elif line.location_id.funcion == 'pasillo06' and order.carrier_id.tipo in [
                                            'ruta', 'horas', 'despacho']:
                                            pasillo06r.append(line)
                                        elif line.location_id.funcion == 'pasillo07' and order.carrier_id.tipo in [
                                            'ruta', 'horas', 'despacho']:
                                            pasillo07r.append(line)
                                        elif line.location_id.funcion == 'pasillo08' and order.carrier_id.tipo in [
                                            'ruta', 'horas', 'despacho']:
                                            pasillo08r.append(line)
                                        elif line.location_id.funcion == 'pasillo09' and order.carrier_id.tipo in [
                                            'ruta', 'horas', 'despacho']:
                                            pasillo09r.append(line)
                                        elif line.location_id.funcion == 'pasillo10' and order.carrier_id.tipo in [
                                            'ruta', 'horas', 'despacho']:
                                            pasillo10r.append(line)
                                        elif line.location_id.funcion == 'pasillo11' and order.carrier_id.tipo in [
                                            'ruta', 'horas', 'despacho']:
                                            pasillo11r.append(line)
                                        elif line.location_id.funcion == 'pasillo12' and order.carrier_id.tipo in [
                                            'ruta', 'horas', 'despacho']:
                                            pasillo12r.append(line)

                            oleada1 = False
                            oleada2 = False
                            oleada3 = False
                            oleada4 = False
                            oleada5 = False
                            oleada6 = False
                            oleada7 = False
                            oleada8 = False
                            oleada9 = False
                            oleada10 = False
                            oleada11 = False
                            oleada12 = False

                            if waveorders <= 6 or (waveorders > 0 and contadororders == numorders) or (
                                    waveorders > 0 and len(orderzone) == 0):
                                waveorders = 0
                                empleadosPicking = self.env["sale.montacargas"].search(
                                    [("activo", "=", True), ("funcion", "!=", "montacargas")])
                                for empl in empleadosPicking:
                                    if empl.funcion == 'pasillo01':
                                        if pas01 is None:
                                            pas01 = empl
                                        else:
                                            if pas01.asignaciones >= empl.asignaciones:
                                                pas01 = empl
                                    elif empl.funcion == 'pasillo02':
                                        if pas02 is None:
                                            pas02 = empl
                                        else:
                                            if pas02.asignaciones >= empl.asignaciones:
                                                pas02 = empl
                                    elif empl.funcion == 'pasillo03':
                                        if pas03 is None:
                                            pas03 = empl
                                        else:
                                            if pas03.asignaciones >= empl.asignaciones:
                                                pas03 = empl
                                    elif empl.funcion == 'pasillo04':
                                        if pas04 is None:
                                            pas04 = empl
                                        else:
                                            if pas04.asignaciones >= empl.asignaciones:
                                                pas04 = empl
                                    elif empl.funcion == 'pasillo05':
                                        if pas05 is None:
                                            pas05 = empl
                                        else:
                                            if pas05.asignaciones >= empl.asignaciones:
                                                pas05 = empl
                                    elif empl.funcion == 'pasillo06':
                                        if pas06 is None:
                                            pas06 = empl
                                        else:
                                            if pas06.asignaciones >= empl.asignaciones:
                                                pas06 = empl
                                    elif empl.funcion == 'pasillo07':
                                        if pas07 is None:
                                            pas07 = empl
                                        else:
                                            if pas07.asignaciones >= empl.asignaciones:
                                                pas07 = empl
                                    elif empl.funcion == 'pasillo08':
                                        if pas08 is None:
                                            pas08 = empl
                                        else:
                                            if pas08.asignaciones >= empl.asignaciones:
                                                pas08 = empl
                                    elif empl.funcion == 'pasillo09':
                                        if pas09 is None:
                                            pas09 = empl
                                        else:
                                            if pas09.asignaciones >= empl.asignaciones:
                                                pas09 = empl
                                    elif empl.funcion == 'pasillo10':
                                        if pas10 is None:
                                            pas10 = empl
                                        else:
                                            if pas10.asignaciones >= empl.asignaciones:
                                                pas10 = empl
                                    elif empl.funcion == 'pasillo11':
                                        if pas11 is None:
                                            pas11 = empl
                                        else:
                                            if pas11.asignaciones >= empl.asignaciones:
                                                pas11 = empl
                                    elif empl.funcion == 'pasillo12':
                                        if pas12 is None:
                                            pas12 = empl
                                        else:
                                            if pas12.asignaciones >= empl.asignaciones:
                                                pas12 = empl

                                oleada1 = addtowave(pas01, pasillo01r, ordersready)
                                oleada2 = addtowave(pas02, pasillo02r, ordersready)
                                oleada3 = addtowave(pas03, pasillo03r, ordersready)
                                oleada4 = addtowave(pas04, pasillo04r, ordersready)
                                oleada5 = addtowave(pas05, pasillo05r, ordersready)
                                oleada6 = addtowave(pas06, pasillo06r, ordersready)
                                oleada7 = addtowave(pas07, pasillo07r, ordersready)
                                oleada8 = addtowave(pas08, pasillo08r, ordersready)
                                oleada9 = addtowave(pas09, pasillo09r, ordersready)
                                oleada10 = addtowave(pas10, pasillo10r, ordersready)
                                oleada11 = addtowave(pas11, pasillo11r, ordersready)
                                oleada12 = addtowave(pas12, pasillo12r, ordersready)

                                pas01 = None
                                pas02 = None
                                pas03 = None
                                pas04 = None
                                pas05 = None
                                pas06 = None
                                pas07 = None
                                pas08 = None
                                pas09 = None
                                pas10 = None
                                pas11 = None
                                pas12 = None

                                pasillo01r = []
                                pasillo02r = []
                                pasillo03r = []
                                pasillo04r = []
                                pasillo05r = []
                                pasillo06r = []
                                pasillo07r = []
                                pasillo08r = []
                                pasillo09r = []
                                pasillo10r = []
                                pasillo11r = []
                                pasillo12r = []

                            if oleada1 or oleada2 or oleada3 or oleada4 or oleada5 or oleada6 or oleada7 or oleada8 or oleada9 or oleada10 or oleada11 or oleada12:
                                orderzone["ocupado"] = True
                                if not order.problema:
                                    order["procesada"] = True
                                    order["a_procesar"] = False
                                    seproceso = True
                                if order.procesada and not self.env["wave.zonas"].search([("orden", "=", order.id), ('ocupado', '=', True)]):
                                    orderzone["orden"] = order.id
                            if seproceso == True:
                                pickaddname = orderzone.name
                                for pick in order.picking_ids:
                                    if "PACK" in pick.name:
                                        empacador = False
                                        funcion = 'empaque'

                                        empleados = self.env['sale.montacargas'].search(
                                            [("activo", "=", True), ("funcion", "=", funcion)])

                                        for empp in empleados:
                                            if not empacador or empacador.asignaciones > empp.asignaciones:
                                                empacador = empp

                                        if empacador:
                                            pick.user_id = empacador.user_id.id
                                            empacador.asignaciones += 1
                                            movzonaz = self.env['stock.picking'].search(
                                                [("origin", "=", pick.origin), ("name", "ilike", pick.name)], limit=1)
                                            ('metodo_de_envio', '=', order.carrier_id.id)
                                            if movzonaz:
                                                movzonaz.user_id = empacador.user_id
                                                zonas_ocupadas = self.env["wave.zonas"].search(
                                                    [("orden", "=", order.id), ('ocupado', '=', True)])
                                                for zon in zonas_ocupadas:
                                                    zon.ocupado = False
                                                orderzone['orden'] = order.id
                                                orderzone['ocupado'] = True
                                                pick["name"] = pick["name"] + ' - ' + pickaddname
                                    if "PICK" in pick.name or "CLH/Z" in pick.name:
                                        if " - " in pick.name:
                                            pickname = pick.name.split(" - ")[0]
                                        else:
                                            pickname = pick.name

                                        pick["name"] = pickname + ' - ' + pickaddname

        if self:
            if reg.carrier_id.warehouse_id.tipo_planeacion != 'automatico':
                config = self.env['filter.order'].create({'almacen': reg.carrier_id.warehouse_id.id})
                config.ejecutar_accion()

    def crear_oleadas_piso(self):
        def addtowavepiso(pas, zona):
            wave = False
            if len(zona) > 0:
                pas["asignaciones"] += 1
                wave = self.env["stock.picking.batch"].create({
                    'picking_type_id': 12,
                    'is_wave': True,
                    'user_id': pas.user_id.id,
                })
                wave["name"] = wave.name + "-EDI"
                for line in zona:
                    # log("Wave " + wave.name + " picking " + str(line.picking_id.name) + " tipo " + str(line.picking_type_id) + " Zona " + line.location_id.complete_name + " Producto " + line.product_id.default_code, level='info')
                    try:
                        line._add_to_wave(wave)
                    except:
                        wave1 = self.env["stock.picking.batch"].create({
                            'picking_type_id': 12,
                            'is_wave': True,
                            'user_id': pas.user_id.id,
                        })
                        line._add_to_wave(wave1)
                        wave1["name"] = wave1.name + "-EDI"

            if wave:
                return wave
            else:
                return False

        ordersready = []
        ordersnotready = []

        ordenes = self.env['sale.order'].search(
            [('state', 'not in', ('draft', 'sent', 'cancel')), ('carrier_id.warehouse_id', '=', self.env['stock.warehouse'].search([('name','=','CALI')]).id),
             ('procesada', '=', False)]).filtered(lambda v: v.delivery_count != 0)

        for reg in ordenes:
            if reg.state in ['sale', 'done']:
                isready = True
                for pick in reg.picking_ids:
                    if pick.state != 'assigned':
                        isready = False
                if isready == True:
                    ordersready.append(reg)
                else:
                    ordersnotready.append(reg)

        if len(ordersready) > 0 or len(ordersnotready) > 0:

            contadororders = 0
            numorders = len(ordersready)
            if numorders > 0:
                for order in ordersready:
                    pis1 = None
                    pis2 = None
                    pis3 = None
                    pis4 = None
                    pis5 = None
                    piso01r = []
                    piso02r = []
                    piso03r = []
                    piso04r = []
                    piso05r = []
                    waveorders = 0
                    empleadosPicking = self.env["sale.montacargas"].search(
                        [("activo", "=", True), ("funcion", "!=", "montacargas")])
                    oleada_piso1 = False
                    oleada_piso2 = False
                    oleada_piso3 = False
                    oleada_piso4 = False
                    oleada_piso5 = False
                    contadororders += 1
                    waveorders += 1

                    for pick in order.picking_ids:

                        if pick.state != 'cancel':
                            # log("Pick name", level='info')
                            for line in pick.move_line_ids:
                                if 'CALI' in order.carrier_id.warehouse_id.name:
                                    if line.location_id.funcion == 'piso01' and order.carrier_id.tipo in [
                                        'pos', 'recogen']:
                                        piso01r.append(line)
                                    elif line.location_id.funcion == 'piso02' and order.carrier_id.tipo in [
                                        'pos', 'recogen']:
                                        piso02r.append(line)
                                    elif line.location_id.funcion == 'piso03' and order.carrier_id.tipo in [
                                        'pos', 'recogen']:
                                        piso03r.append(line)
                                    elif line.location_id.funcion == 'piso04' and order.carrier_id.tipo in [
                                        'pos', 'recogen']:
                                        piso04r.append(line)
                                    elif line.location_id.funcion == 'piso05' and order.carrier_id.tipo in [
                                        'pos', 'recogen']:
                                        piso05r.append(line)

                        for empl in empleadosPicking:
                            if empl.funcion == 'piso01':
                                if pis1 is None:
                                    pis1 = empl
                                else:
                                    if pis1.asignaciones >= empl.asignaciones:
                                        pis1 = empl
                            elif empl.funcion == 'piso02':
                                if pis2 is None:
                                    pis2 = empl
                                else:
                                    if pis2.asignaciones >= empl.asignaciones:
                                        pis2 = empl
                            elif empl.funcion == 'piso03':
                                if pis3 is None:
                                    pis3 = empl
                                else:
                                    if pis3.asignaciones >= empl.asignaciones:
                                        pis3 = empl
                            elif empl.funcion == 'piso04':
                                if pis4 is None:
                                    pis4 = empl
                                else:
                                    if pis4.asignaciones >= empl.asignaciones:
                                        pis4 = empl
                            elif empl.funcion == 'piso05':
                                if pis5 is None:
                                    pis5 = empl
                                else:
                                    if pis5.asignaciones >= empl.asignaciones:
                                        pis5 = empl

                        oleada_piso1 = addtowavepiso(pis1, piso01r)
                        oleada_piso2 = addtowavepiso(pis2, piso02r)
                        oleada_piso3 = addtowavepiso(pis3, piso03r)
                        oleada_piso4 = addtowavepiso(pis4, piso04r)
                        oleada_piso5 = addtowavepiso(pis5, piso05r)

                    if oleada_piso1 or oleada_piso2 or oleada_piso3 or oleada_piso4 or oleada_piso5:
                        # Marcar la orden como procesada solo después de crear la oleada
                        order["procesada"] = True
                        order["a_procesar"] = False

        if self:
            if reg.carrier_id.warehouse_id.tipo_planeacion != 'automatico':
                config = self.env['filter.order'].create({'almacen': reg.carrier_id.warehouse_id.id})
                config.ejecutar_accion()

    def clh_turbo(self):
        for reg in self:
            if reg.num_turbo:
                lineas = reg.num_turbo
            else:
                return
            procesado = False
            if len(reg.order_line) <= lineas and reg.carrier_id.tipo in ['ruta', 'horas', 'despacho']:
                # Crear una oleada para esta orden de venta
                batch = False
                availablezones = self.env["wave.zonas"].search(
                    [("ocupado", "=", False), ('metodo_de_envio', '=', reg.carrier_id.id)])
                if availablezones:

                    for pick in reg.picking_ids:
                        batch = False
                        if "CLH/Z" in pick.name or "PACK" in pick.name:
                            procesado = True
                            empacador = False  # Variable para empleados de packing/picking
                            movzonaz = None  # Movimiento relacionado
                            funcion = 'turbo'
                            if "PACK" in pick.name:
                                funcion = 'turbo_empaque'

                            # Obtener empleados activos según la función
                            empleados = self.env['sale.montacargas'].search(
                                [("activo", "=", True), ("funcion", "=", funcion)])

                            # Seleccionar el empleado con menos asignaciones
                            for empp in empleados:
                                if not empacador or empacador.asignaciones > empp.asignaciones:
                                    empacador = empp

                            # Asignar empleado si se encontró uno
                            if empacador:
                                pick.user_id = empacador.user_id.id
                                empacador.asignaciones += 1
                                # Relacionar movimiento de zona Z
                                movzonaz = self.env['stock.picking'].search(
                                    [("origin", "=", pick.origin), ("name", "ilike", pick.name)], limit=1)
                                if movzonaz:
                                    movzonaz.user_id = empacador.user_id
                                    pickaddname = availablezones[0].name
                                    availablezones[0].ocupado = True
                                    availablezones[0].orden = reg
                                    pick["name"] = pick["name"] + ' - ' + pickaddname

                        elif "PICK" in pick.name and pick.state == 'assigned':
                            procesado = True
                            empacador = False  # Variable para empleados de packing/picking
                            movzonaz = None  # Movimiento relacionado
                            # Obtener empleados para picking
                            empleados_picking = self.env['sale.montacargas'].search(
                                [("activo", "=", True), ("funcion", "=", 'turbo')])

                            if empleados_picking:
                                batch = self.env['stock.picking.batch'].create({
                                    'picking_type_id': 3,
                                    'is_wave': True,
                                    'user_id': empleados_picking[0].user_id.id,
                                    'picking_ids': pick.ids
                                })

                                for empp in empleados_picking:
                                    if not empacador or empacador.asignaciones > empp.asignaciones:
                                        empacador = empp

                                if empacador:
                                    pick.user_id = empacador.user_id.id
                                    empacador.asignaciones += 1

                        # Agregar el picking a la oleada
                        if batch:
                            if empacador:
                                batch.user_id = empacador.user_id.id
                            pickaddname = 'TURBO-' + availablezones[0].name
                            availablezones[0].ocupado = True
                            if not reg.problema and not self.env["wave.zonas"].search([("orden", "=", reg.id), ('ocupado', '=', True)]):
                                availablezones[0].orden = reg
                            pick["name"] = pick["name"] + ' - ' + pickaddname
                            batch.name += '-TURBO'
                            batch.state = 'in_progress'
                            batch.actualizar_campos_ordenes()

                    # Marcar como procesada la orden si hubo procesamiento
                    if procesado:
                        if not reg.problema:
                            reg.procesada = True

        if self:
            if reg.carrier_id.warehouse_id.tipo_planeacion != 'automatico':
                config = self.env['filter.order'].create({'almacen': reg.carrier_id.warehouse_id.id})
                config.ejecutar_accion()

    def clh_mkp(self):
        for reg in self:
            procesado = False
            if len(reg.order_line) <= 7 and reg.carrier_id.tipo in ['marketplace']:
                # Crear una oleada para esta orden de venta
                batch = False
                availablezones = self.env["wave.zonas"].search(
                    [("ocupado", "=", False), ('metodo_de_envio', '=', reg.carrier_id)])
                if availablezones:

                    for pick in reg.picking_ids:
                        batch = False
                        if "CLH/Z" in pick.name or "PACK" in pick.name:
                            procesado = True
                            empacador = False  # Variable para empleados de packing/picking
                            movzonaz = None  # Movimiento relacionado
                            funcion = 'mkp'
                            if "PACK" in pick.name:
                                funcion = 'mkp_empaque'

                            # Obtener empleados activos según la función
                            empleados = self.env['sale.montacargas'].search(
                                [("activo", "=", True), ("funcion", "=", funcion)])

                            # Seleccionar el empleado con menos asignaciones
                            for empp in empleados:
                                if not empacador or empacador.asignaciones > empp.asignaciones:
                                    empacador = empp

                            # Asignar empleado si se encontró uno
                            if empacador:
                                pick.user_id = empacador.user_id.id
                                empacador.asignaciones += 1
                                # Relacionar movimiento de zona Z
                                movzonaz = self.env['stock.picking'].search(
                                    [("origin", "=", pick.origin), ("name", "ilike", pick.name)], limit=1)
                                if movzonaz:
                                    movzonaz.user_id = empacador.user_id
                                    pickaddname = availablezones[0].name
                                    availablezones[0].ocupado = True
                                    if not reg.problema  and not self.env["wave.zonas"].search([("orden", "=", reg.id), ('ocupado', '=', True)]):
                                        availablezones[0].orden = reg
                                    pick["name"] = pick["name"] + ' - ' + pickaddname


                        elif "PICK" in pick.name and pick.state == 'assigned':
                            procesado = True
                            empacador = False  # Variable para empleados de packing/picking
                            movzonaz = None  # Movimiento relacionado
                            # Obtener empleados para picking
                            empleados_picking = self.env['sale.montacargas'].search(
                                [("activo", "=", True), ("funcion", "=", 'mkp')])

                            if empleados_picking:
                                batch = self.env['stock.picking.batch'].create({
                                    'picking_type_id': 3,
                                    'is_wave': True,
                                    'user_id': empleados_picking[0].user_id.id,
                                })

                                for empp in empleados_picking:
                                    if not empacador or empacador.asignaciones > empp.asignaciones:
                                        empacador = empp

                                if empacador:
                                    pick.user_id = empacador.user_id.id
                                    empacador.asignaciones += 1

                        # Agregar el picking a la oleada
                        if batch:
                            if empacador:
                                batch.user_id = empacador.user_id.id
                            batch.picking_ids += pick
                            pickaddname = 'MKP-' + availablezones[0].name
                            availablezones[0].ocupado = True
                            availablezones[0].orden = reg
                            pick["name"] = pick["name"] + ' - ' + pickaddname
                            batch.state = 'in_progress'
                            batch.name += '-MKP'
                            batch.actualizar_campos_ordenes()

                    # Marcar como procesada la orden si hubo procesamiento
                    if procesado:
                        if not reg.problema:
                            reg.procesada = True

        if self:
            if reg.carrier_id.warehouse_id.tipo_planeacion != 'automatico':
                config = self.env['filter.order'].create({'almacen': reg.carrier_id.warehouse_id.id})
                config.ejecutar_accion()

    def clh_flex(self):
        for reg in self:
            procesado = False
            if reg.carrier_id.tipo in ['flex']:
                # Crear una oleada para esta orden de venta
                batch = False
                availablezones = self.env["wave.zonas"].search(
                    [("ocupado", "=", False), ('metodo_de_envio', '=', reg.carrier_id.id)])
                if availablezones:

                    for pick in reg.picking_ids:
                        batch = False
                        if "CLH/Z" in pick.name or "PACK" in pick.name:
                            procesado = True
                            empacador = False  # Variable para empleados de packing/picking
                            movzonaz = None  # Movimiento relacionado
                            funcion = 'flex'
                            if "PACK" in pick.name:
                                funcion = 'flex_empaque'

                            # Obtener empleados activos según la función
                            empleados = self.env['sale.montacargas'].search(
                                [("activo", "=", True), ("funcion", "=", funcion)])

                            # Seleccionar el empleado con menos asignaciones
                            for empp in empleados:
                                if not empacador or empacador.asignaciones > empp.asignaciones:
                                    empacador = empp

                            # Asignar empleado si se encontró uno
                            if empacador:
                                # Relacionar movimiento de zona Z
                                movzonaz = self.env['stock.picking'].search(
                                    [("origin", "=", pick.origin), ("name", "ilike", pick.name)], limit=1)
                                if movzonaz:
                                    movzonaz.user_id = empacador.user_id
                                    pickaddname = availablezones[0].name
                                    availablezones[0].ocupado = True
                                    if not reg.problema and not self.env["wave.zonas"].search([("orden", "=", reg.id), ('ocupado', '=', True)]):
                                        availablezones[0].orden = reg
                                        pick.user_id = empacador.user_id.id
                                        pick["name"] = pick["name"] + ' - ' + pickaddname
                                        empacador.asignaciones += 1

                        elif "PICK" in pick.name and pick.state == 'assigned':
                            procesado = True
                            empacador = False  # Variable para empleados de packing/picking
                            movzonaz = None  # Movimiento relacionado
                            # Obtener empleados para picking
                            empleados_picking = self.env['sale.montacargas'].search(
                                [("activo", "=", True), ("funcion", "=", 'flex')])

                            if empleados_picking:
                                batch = self.env['stock.picking.batch'].create({
                                    'picking_type_id': 3,
                                    'is_wave': True,
                                    'user_id': empleados_picking[0].user_id.id,
                                })

                                for empp in empleados_picking:
                                    if not empacador or empacador.asignaciones > empp.asignaciones:
                                        empacador = empp

                                if empacador:
                                    pick.user_id = empacador.user_id.id
                                    empacador.asignaciones += 1

                        # Agregar el picking a la oleada
                        if batch:
                            if empacador:
                                batch.user_id = empacador.user_id.id
                            batch.picking_ids += pick
                            pickaddname = 'FLEX-' + availablezones[0].name
                            availablezones[0].ocupado = True
                            availablezones[0].orden = reg
                            pick["name"] = pick["name"] + ' - ' + pickaddname
                            batch.state = 'in_progress'
                            batch.name += '-FLEX'
                            batch.actualizar_campos_ordenes()

                    # Marcar como procesada la orden si hubo procesamiento
                    if procesado:
                        if not reg.problema:
                            reg.procesada = True

        if self:
            if reg.carrier_id.warehouse_id.tipo_planeacion != 'automatico':
                config = self.env['filter.order'].create({'almacen': reg.carrier_id.warehouse_id.id})
                config.ejecutar_accion()

    def contar_productos(self):
        productos = len(self.order_line.move_ids)
        return productos

    def sumar_ordenes(self):
        suma = 0
        for record in self.order_line.order_id:
            suma += record.amount_untaxed
        return suma

    def create(self, vals):
        record = super().create(vals)
        record.numero_items = len(record.order_line)
        return record

    @api.constrains('order_line')
    def onchange_order_line_num(self):
        for record in self:
            record.numero_items = len(record.order_line)

    @api.constrains('state')
    def onchange_state(self):
        for record in self:
            record.numero_items = len(record.order_line)

