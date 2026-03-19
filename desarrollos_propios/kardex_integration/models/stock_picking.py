import requests
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
from collections import defaultdict

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'
    estado_confirmado_kardex = fields.Boolean("Confirmado Kardex", default=False)
    external_line_id = fields.Char("ID Externo de Línea")
    kardex_identificador = fields.Integer("Identificador Kardex")
    

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    kardex_sent = fields.Boolean("Enviado a Kardex", default=False)
    external_id_kardex = fields.Char("ID externo albarán")

    def action_sync_kardex(self):
        config = self.env['ir.config_parameter'].sudo()
        url_insert = config.get_param('kardex.url.insert')

        if not url_insert:
            raise UserError("Falta configurar la URL de inserción para Kardex.")

        for picking in self:
            if not picking.external_id_kardex:
                picking.external_id_kardex = str(picking.id)
                
            display_name = picking.picking_type_id.display_name or ""
            info1 = display_name.split(":")[0].strip() if ":" in display_name else display_name
            for move in picking.move_ids_without_package:
                if not move.product_id.default_code:
                    raise UserError(f"El producto '{move.product_id.display_name}' no tiene código interno.")
                try:
                    qty = float(move.quantity)
                    if qty < 0:
                        raise UserError(f"La cantidad no puede ser negativa: {qty}")
                    qty_int = int(round(qty))
                except (ValueError, TypeError) as e:
                    raise UserError(f"Cantidad inválida para '{move.product_id.display_name}': {move.qty_done}\nError: {str(e)}")

                payload = {
                    "orden": picking.name,
                    "tipo": "2",
                    "info1": info1,
                    "info2": str(picking.id) or "",
                    "info3": ".",
                    "info4": ".",
                    "info5": ".",
                    "infoline1": str(move.id) or "",
                    "infoline2": ".",
                    "infoline3": ".",
                    "infoline4": ".",
                    "infoline5": ".",
                    "material": move.product_id.default_code,
                    "cantidad": qty_int,
                }

                try:
                    headers = {'Content-Type': 'application/json'}
                    res = requests.post(url_insert, json=payload, headers=headers, timeout=10)
                    res.raise_for_status()
                except Exception as e:
                    raise UserError(f"❌ Error al enviar producto '{move.product_id.display_name}' a Kardex:\n{str(e)}")

            picking.kardex_sent = True
            picking.message_post(body="✅ Todos los productos fueron enviados a Kardex correctamente.")

    def action_sync_kardex_in(self):
        config = self.env['ir.config_parameter'].sudo()
        url_insert = config.get_param('kardex.url.insert')

        if not url_insert:
            raise UserError("Falta configurar la URL de inserción para Kardex.")

        for picking in self:
            if not picking.external_id_kardex:
                picking.external_id_kardex = str(picking.id)
                
            display_name = picking.picking_type_id.display_name or ""
            info1 = display_name.split(":")[0].strip() if ":" in display_name else display_name
            for move in picking.move_ids_without_package:
                if not move.product_id.default_code:
                    raise UserError(f"El producto '{move.product_id.display_name}' no tiene código interno.")
                try:
                    qty = float(move.quantity)
                    if qty < 0:
                        raise UserError(f"La cantidad no puede ser negativa: {qty}")
                    qty_int = int(round(qty))
                except (ValueError, TypeError) as e:
                    raise UserError(f"Cantidad inválida para '{move.product_id.display_name}': {move.qty_done}\nError: {str(e)}")

                payload = {
                    "orden": picking.name,
                    "tipo": "1",  # ← TIPO IN
                    "info1": info1,
                    "info2": str(picking.id) or "",
                    "info3": ".",
                    "info4": ".",
                    "info5": ".",
                    "infoline1": str(move.id) or "",
                    "infoline2": ".",
                    "infoline3": ".",
                    "infoline4": ".",
                    "infoline5": ".",
                    "material": move.product_id.default_code,
                    "cantidad": qty_int,
                }

                try:
                    headers = {'Content-Type': 'application/json'}
                    res = requests.post(url_insert, json=payload, headers=headers, timeout=10)
                    res.raise_for_status()
                except Exception as e:
                    raise UserError(f"❌ Error al enviar producto '{move.product_id.display_name}' a Kardex (IN):\n{str(e)}")

            picking.kardex_sent = True
            picking.message_post(body="✅ Todos los productos fueron enviados a Kardex IN correctamente.")

    @api.model
    def cron_check_kardex_output(self):
        config = self.env['ir.config_parameter'].sudo()
        base_url = config.get_param('kardex.url.lectura')  # e.g. https://n8n.tooliahoyostools.com/webhook/...

        if not base_url:
            _logger.warning("❌ URL base de lectura de Kardex no está configurada.")
            return

        for tipo in [1, 2]:
            estado = 2  # Estado confirmado
            try:
                # Construcción de URL final
                full_url = f"{base_url}/status/{estado}/{tipo}"
                _logger.info("🧾 Iniciando lectura de Kardex OUTPUT...")
                _logger.info(f"📡 Enviando solicitud a: {full_url}")

                headers = {'Content-Type': 'application/json'}
                res = requests.get(full_url, headers=headers, timeout=15)
                res.raise_for_status()
                data = res.json()
                _logger.info(f"✅ Datos recibidos de Kardex (tipo {tipo}): {json.dumps(data, indent=2)}")

                # Agrupar respuestas por ORDEN
                ordenes = {}
                for linea in data:
                    _logger.info(f"🔄 Procesando línea: {json.dumps(linea, indent=2)}")
                    orden = linea.get("ORDEN")
                    if orden:
                        ordenes.setdefault(orden, []).append(linea)

                for orden_name, lineas in ordenes.items():
                    _logger.info(f"🔎 Buscando picking con nombre: {orden_name}")
                    picking = self.env['stock.picking'].search([('name', '=', orden_name)], limit=1)

                    if not picking:
                        _logger.warning(f"⚠️ No se encontró picking con nombre: {orden_name}")
                        continue
                    _logger.info(f"✅ Picking encontrado: {picking.name}, estado: {picking.state}")

                    if picking.state == 'done':
                        _logger.info(f"🔒 Picking {picking.name} ya está validado. Se omite.")
                        continue

                    if all(int(line.get("ESTADO", 0)) == 2 for line in lineas):
                        for line in lineas:
                            material = line.get("MATERIAL")
                            estado = int(line.get("ESTADO", 0))
                            cantidad_real = int(float(line.get("CANTIDAD", 0)))
                            linea_externa = line.get("INFOLINE1")
                            linea_identificador = line.get("ID")

                            _logger.info(f"🔍 Línea material: {material}, estado: {estado}, cantidad: {cantidad_real}, línea externa: {linea_externa}, identificador: {linea_identificador}")

                            if not linea_externa:
                                _logger.warning("⚠️ Línea sin INFOLINE1. Se omite.")
                                continue

                            move = picking.move_ids_without_package.filtered(lambda m: str(m.id) == str(linea_externa))
                            if move:
                                _logger.info(f"🔁 Línea Odoo encontrada para ID externo {linea_externa}: move_id={move.ids}")
                            else:
                                _logger.warning(f"⚠️ No se encontró línea Odoo para ID externo {linea_externa}")
                                continue

                            for m in move:
                                m.quantity = cantidad_real
                                if estado == 2:
                                    m.estado_confirmado_kardex = True
                                if linea_identificador:
                                    m.kardex_identificador = int(linea_identificador)
                                    _logger.info(f"📌 Identificador Kardex guardado: {m.kardex_identificador}")
                                else:
                                    _logger.warning(f"⚠️ Línea {m.id} no tiene identificador Kardex en la respuesta.")

                        try:
                            if all(m.estado_confirmado_kardex for m in picking.move_ids_without_package):
                                _logger.info(f"✅ Todas las líneas confirmadas por Kardex. Validando picking {picking.name}...")
                                picking.with_context(skip_backorder=True).button_validate()
                                picking.message_post(body="✅ Kardex confirmó todas las líneas. Albarán validado automáticamente.")

                                backorder = self.env['stock.picking'].search([
                                    ('backorder_id', '=', picking.id),
                                    ('state', 'in', ['confirmed', 'assigned', 'waiting'])
                                ], limit=1)
                                if backorder:
                                    backorder.action_cancel()
                                    _logger.info(f"❎ Backorder cancelado para albarán {picking.name}")

                                picking.send_kardex_estado_final()
                        except Exception as e:
                            _logger.error(f"❌ Error al validar albarán {orden_name}: {e}")
                    else:
                        _logger.info(f"⏳ Kardex aún no ha confirmado todas las líneas para {orden_name}")

            except Exception as e:
                _logger.error(f"❌ Error al consultar Kardex OUTPUT para tipo {tipo}: {e}")
            
    def send_kardex_estado_final(self):
        self.ensure_one()
        config = self.env['ir.config_parameter'].sudo()
        url_update = config.get_param('kardex.url.update')

        if not url_update:
            _logger.warning("⚠️ URL de actualización de estado Kardex no está configurada.")
            return

        for move in self.move_ids_without_package:
            if not move.kardex_identificador:
                _logger.warning(f"⚠️ Línea {move.id} sin identificador de Kardex.")
                continue

            payload = {
                "identificador": move.kardex_identificador
            }

            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url_update, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                _logger.info(f"✅ Estado final enviado a Kardex para línea {move.id} (Identificador: {move.kardex_identificador})")
            except Exception as e:
                _logger.error(f"❌ Error al enviar estado final a Kardex para línea {move.id}: {e}")
