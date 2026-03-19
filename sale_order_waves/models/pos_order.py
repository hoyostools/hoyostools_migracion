from odoo import fields, models, api, _

class PosOrderWave(models.Model):
    _inherit = 'pos.order'

    def _process_saved_order(self, draft):
        res = super()._process_saved_order(draft)
        self.crear_oleadas_piso_pos()
        return res

    def crear_oleadas_piso_pos(self):

        def add_to_wave_pos(pas, zona):
            wave = False
            if len(zona) > 0:
                pas["asignaciones"] += 1
                wave = self.env["stock.picking.batch"].create({
                    'picking_type_id': 12,
                    'is_wave': True,
                    'user_id': pas.user_id.id,
                })
                wave["name"] = wave.name + "-PTV"
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
                        wave1["name"] = wave1.name + "-PTV"

            if wave:
                return wave
            else:
                return False

        ordersready = []
        ordersnotready = []

        ordenes = self

        for reg in ordenes:
            if reg.config_id:
                if reg.config_id.route_id.oleada_pos == True and reg.config_id.warehouse_id.oleada_pos == True and reg.config_id.ship_later == True and reg.config_id.picking_policy == 'direct' and reg.config_id.picking_type_id.warehouse_id.oleada_pos == True:
                    ordersready.append(reg)

        if len(ordersready) > 0:

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
                                if line.location_id.funcion == 'piso01':
                                    piso01r.append(line)
                                elif line.location_id.funcion == 'piso02':
                                    piso02r.append(line)
                                elif line.location_id.funcion == 'piso03':
                                    piso03r.append(line)
                                elif line.location_id.funcion == 'piso04':
                                    piso04r.append(line)
                                elif line.location_id.funcion == 'piso05':
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

                        oleada_piso1 = add_to_wave_pos(pis1, piso01r)
                        oleada_piso2 = add_to_wave_pos(pis2, piso02r)
                        oleada_piso3 = add_to_wave_pos(pis3, piso03r)
                        oleada_piso4 = add_to_wave_pos(pis4, piso04r)
                        oleada_piso5 = add_to_wave_pos(pis5, piso05r)

                    if oleada_piso1 or oleada_piso2 or oleada_piso3 or oleada_piso4 or oleada_piso5:
                        return