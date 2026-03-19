from odoo import models, api, fields
import re
from odoo import _
import logging
from pytz import timezone

from odoo.exceptions import ValidationError

tz = timezone('America/Bogota')
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    procesado_productividad = fields.Boolean(string="Procesado para Productividad", default=False)

    def _get_product_count(self):
        return len(set(self.move_ids_without_package.mapped('product_id.id')))

    def _get_picking_points(self):
        puntos = 0.0
        if self.origin:
            sale_order = self.env['sale.order'].search([('name', '=', self.origin)], limit=1)
            if sale_order:
                puntos = sale_order.amount_untaxed / 1_000_000.0
        return puntos

    def create_seguimiento_empacador(self):

        Seguimiento = self.env['productividad.seguimiento_empacador']
        TableroConfig = self.env['productividad.tablero_configuracion']
        SaleOrder = self.env['sale.order']
        ResumenMensual = self.env['productividad.resumen_empacador_mensual'].sudo()

        for picking in self:

            if not picking.origin or picking.procesado_productividad:
                continue

            if picking.picking_type_id.name != 'Empaquetar' or not picking.user_id:
                continue

            responsable = picking.user_id

            fecha_dt = (picking.date_done or picking.create_date).astimezone(tz)
            fecha = fecha_dt.date()

            configuracion = TableroConfig.search([
                ('user_id', '=', responsable.id),
                ('funcion', '=', 'empacador')
            ], limit=1)

            if not configuracion or not configuracion.turno_id:
                continue

            turno = configuracion.turno_id

            sale_order = SaleOrder.search(
                [('name', '=', picking.origin)],
                limit=1
            )

            productos_unicos = set()
            kits_procesados = set()
            puntos = 0.0

            for move in picking.move_ids_without_package:

                quantity = sum(move.move_line_ids.mapped('quantity')) or 0.0
                if quantity <= 0:
                    continue

                # ===============================
                # 🟣 KIT
                # ===============================
                if move.description_bom_line:

                    full_desc = move.description_bom_line.strip()

                    # 🔥 Extraer código entre []
                    match = re.search(r'\[(.*?)\]', full_desc)
                    if match:
                        kit_code = match.group(1).strip()
                    else:
                        kit_code = full_desc.split(':')[0].strip()

                    if kit_code in kits_procesados:
                        continue

                    kits_procesados.add(kit_code)

                    if sale_order:
                        line = sale_order.order_line.filtered(
                            lambda l:
                                (l.product_id.default_code and kit_code in l.product_id.default_code)
                                or kit_code in l.name
                        )

                        if line:
                            puntos += line[0].price_subtotal

                # ===============================
                # 🔵 PRODUCTO NORMAL
                # ===============================
                else:

                    product = move.product_id
                    productos_unicos.add(product.id)

                    if "OP" in picking.origin:
                        puntos += quantity * product.standard_price

                    elif sale_order:
                        line = sale_order.order_line.filtered(
                            lambda l: l.product_id.id == product.id
                        )

                        if line and line[0].product_uom_qty:
                            unit_value = (
                                line[0].price_subtotal /
                                line[0].product_uom_qty
                            )
                            puntos += quantity * unit_value

            # 🔥 NORMALIZAR
            puntos_normalizados = puntos / 1_000_000.0

            total_items = len(productos_unicos) + len(kits_procesados)

            seguimiento = Seguimiento.search([
                ('user_id', '=', responsable.id),
                ('fecha', '=', fecha),
                ('turno_id', '=', turno.id),
            ], limit=1)

            if seguimiento:
                seguimiento.write({
                    'items': seguimiento.items + total_items,
                    'documentos': seguimiento.documentos + 1,
                    'puntos': seguimiento.puntos + puntos_normalizados,
                    'cajas_usadas': seguimiento.cajas_usadas + (picking.cajas_usadas or 0),
                    'cantidad_maxima_cajas': seguimiento.cantidad_maxima_cajas + (picking.cantidad_maxima_cajas or 0),
                    'ahorro': seguimiento.ahorro + (picking.ahorro or 0.0),
                })
            else:
                Seguimiento.create({
                    'user_id': responsable.id,
                    'fecha': fecha,
                    'turno_id': turno.id,
                    'items': total_items,
                    'documentos': 1,
                    'puntos': puntos_normalizados,
                    'cajas_usadas': picking.cajas_usadas or 0,
                    'cantidad_maxima_cajas': picking.cantidad_maxima_cajas or 0,
                    'ahorro': picking.ahorro or 0.0,
                })

            # 🔹 Asegurar resumen mensual
            mes = fecha.month
            anio = fecha.year

            resumen = ResumenMensual.search([
                ('user_id', '=', responsable.id),
                ('mes', '=', mes),
                ('anio', '=', anio),
            ], limit=1)

            if not resumen:
                ResumenMensual.create({
                    'user_id': responsable.id,
                    'mes': mes,
                    'anio': anio,
                })

            picking.procesado_productividad = True


    def create_seguimiento_picking(self):

        Seguimiento = self.env['productividad.seguimiento_picking']
        TableroConfig = self.env['productividad.tablero_configuracion']
        SaleOrder = self.env['sale.order']

        batch_processed = set()

        for picking in self:

            if not picking.origin or picking.procesado_productividad:
                continue

            if picking.picking_type_id.name != 'Recolectar':
                continue

            fecha_dt = (picking.date_done or picking.create_date).astimezone(tz)
            fecha = fecha_dt.date()

            # ==================================================
            # 🔁 CASO WAVE
            # ==================================================
            if picking.batch_id and picking.batch_id.id not in batch_processed:

                batch = picking.batch_id
                responsable = batch.user_id

                if not responsable:
                    continue

                configuracion = TableroConfig.search([
                    ('user_id', '=', responsable.id),
                    ('funcion', '=', 'separador')
                ], limit=1)

                if not configuracion or not configuracion.turno_id:
                    continue

                turno = configuracion.turno_id

                productos_unicos = set()
                kits_procesados = set()
                puntos = 0.0

                for pick in batch.picking_ids.filtered(
                    lambda p: p.picking_type_id.name == 'Recolectar'
                    and not p.procesado_productividad
                ):

                    sale_order = SaleOrder.search(
                        [('name', '=', pick.origin)],
                        limit=1
                    )

                    for move in pick.move_ids_without_package:

                        quantity = sum(move.move_line_ids.mapped('quantity')) or 0.0
                        if quantity <= 0:
                            continue

                        # ===============================
                        # 🟣 KIT
                        # ===============================
                        if move.description_bom_line:

                            full_desc = move.description_bom_line.strip()

                            match = re.search(r'\[(.*?)\]', full_desc)
                            if match:
                                kit_code = match.group(1).strip()
                            else:
                                kit_code = full_desc.split(':')[0].strip()

                            if kit_code in kits_procesados:
                                continue

                            kits_procesados.add(kit_code)

                            if sale_order:
                                line = sale_order.order_line.filtered(
                                    lambda l:
                                        (l.product_id.default_code and kit_code in l.product_id.default_code)
                                        or kit_code in l.name
                                )
                                if line:
                                    puntos += line[0].price_subtotal

                        # ===============================
                        # 🔵 PRODUCTO NORMAL
                        # ===============================
                        else:

                            product = move.product_id
                            productos_unicos.add(product.id)

                            if 'OP' in pick.origin:
                                puntos += quantity * product.standard_price

                            elif sale_order:
                                line = sale_order.order_line.filtered(
                                    lambda l: l.product_id.id == product.id
                                )
                                if line and line[0].product_uom_qty:
                                    unit_value = (
                                        line[0].price_subtotal /
                                        line[0].product_uom_qty
                                    )
                                    puntos += quantity * unit_value

                    pick.procesado_productividad = True

                puntos_normalizados = puntos / 1_000_000.0
                total_items = len(productos_unicos) + len(kits_procesados)

                seguimiento = Seguimiento.search([
                    ('user_id', '=', responsable.id),
                    ('fecha', '=', fecha),
                    ('turno_id', '=', turno.id),
                ], limit=1)

                if seguimiento:
                    seguimiento.write({
                        'items': seguimiento.items + total_items,
                        'documentos': seguimiento.documentos + 1,
                        'puntos': seguimiento.puntos + puntos_normalizados,
                    })
                else:
                    Seguimiento.create({
                        'user_id': responsable.id,
                        'fecha': fecha,
                        'turno_id': turno.id,
                        'items': total_items,
                        'documentos': 1,
                        'puntos': puntos_normalizados,
                    })

                batch_processed.add(batch.id)

            # ==================================================
            # 🔁 CASO INDIVIDUAL
            # ==================================================
            elif not picking.batch_id:

                responsable = picking.user_id
                if not responsable:
                    continue

                configuracion = TableroConfig.search([
                    ('user_id', '=', responsable.id),
                    ('funcion', '=', 'separador')
                ], limit=1)

                if not configuracion or not configuracion.turno_id:
                    continue

                turno = configuracion.turno_id

                sale_order = SaleOrder.search(
                    [('name', '=', picking.origin)],
                    limit=1
                )

                productos_unicos = set()
                kits_procesados = set()
                puntos = 0.0

                for move in picking.move_ids_without_package:

                    quantity = sum(move.move_line_ids.mapped('quantity')) or 0.0
                    if quantity <= 0:
                        continue

                    if move.description_bom_line:

                        full_desc = move.description_bom_line.strip()
                        match = re.search(r'\[(.*?)\]', full_desc)
                        if match:
                            kit_code = match.group(1).strip()
                        else:
                            kit_code = full_desc.split(':')[0].strip()

                        if kit_code in kits_procesados:
                            continue

                        kits_procesados.add(kit_code)

                        if sale_order:
                            line = sale_order.order_line.filtered(
                                lambda l:
                                    (l.product_id.default_code and kit_code in l.product_id.default_code)
                                    or kit_code in l.name
                            )
                            if line:
                                puntos += line[0].price_subtotal

                    else:
                        product = move.product_id
                        productos_unicos.add(product.id)

                        if 'OP' in picking.origin:
                            puntos += quantity * product.standard_price

                        elif sale_order:
                            line = sale_order.order_line.filtered(
                                lambda l: l.product_id.id == product.id
                            )
                            if line and line[0].product_uom_qty:
                                unit_value = (
                                    line[0].price_subtotal /
                                    line[0].product_uom_qty
                                )
                                puntos += quantity * unit_value

                puntos_normalizados = puntos / 1_000_000.0
                total_items = len(productos_unicos) + len(kits_procesados)

                seguimiento = Seguimiento.search([
                    ('user_id', '=', responsable.id),
                    ('fecha', '=', fecha),
                    ('turno_id', '=', turno.id),
                ], limit=1)

                if seguimiento:
                    seguimiento.write({
                        'items': seguimiento.items + total_items,
                        'documentos': seguimiento.documentos + 1,
                        'puntos': seguimiento.puntos + puntos_normalizados,
                    })
                else:
                    Seguimiento.create({
                        'user_id': responsable.id,
                        'fecha': fecha,
                        'turno_id': turno.id,
                        'items': total_items,
                        'documentos': 1,
                        'puntos': puntos_normalizados,
                    })

                picking.procesado_productividad = True

                
    def _get_turno_por_fecha(self, fecha_dt):
        Turno = self.env['productividad.turno']
        turnos = Turno.search([])

        if not fecha_dt:
            return False

        hora_actual = fecha_dt.hour + (fecha_dt.minute / 60.0)

        for turno in turnos:
            if turno.hora_inicio < turno.hora_fin:
                if turno.hora_inicio <= hora_actual < turno.hora_fin:
                    return turno
            else:
                if hora_actual >= turno.hora_inicio or hora_actual < turno.hora_fin:
                    return turno

        return False
    
    def _get_turno_from_configuracion(self, user, funcion, fecha_dt):
        """
        Obtiene el turno desde la configuración del usuario.
        Si no existe configuración, usa la lógica por hora.
        """
        self.ensure_one()

        configuracion = self.env['productividad.tablero_configuracion'].search([
            ('user_id', '=', user.id),
            ('funcion', '=', funcion)
        ], limit=1)

        if configuracion and configuracion.turno_id:
            return configuracion.turno_id

        # Fallback opcional por hora
        return self._get_turno_por_fecha(fecha_dt)

    def button_validate(self):
        res = super().button_validate()
        # Aseguramos que el método se aplique individualmente
        for picking in self:
            picking.create_seguimiento_empacador()
            picking.create_seguimiento_picking()
        return res
