from odoo import models, fields
from odoo.exceptions import UserError
import requests

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    kardex_url_insert = fields.Char(string="URL Insertar", config_parameter="kardex.url.insert")
    kardex_url_lectura = fields.Char(string="URL Lectura", config_parameter="kardex.url.lectura")
    kardex_url_update = fields.Char(string="URL de Actualización Kardex", config_parameter="kardex.url.update")

    def action_test_insert_connection(self):
        if not self.kardex_url_insert:
            raise UserError("Falta la URL de inserción")

        payload = {
            "orden": "TEST123",
            "prioridad": 1,
            "almacen": "Test WH",
            "tipo": 2,
            "info1": "Prueba de conexión desde Odoo",
            "lineas": [
                {"linea": 1, "material": "TEST", "cantidad": 1, "lote": "LOTE123"}
            ]
        }

        try:
            headers = {'Content-Type': 'application/json'}
            res = requests.post(self.kardex_url_insert, json=payload, headers=headers, timeout=10)
            res.raise_for_status()
            return self._display_notification("Conexión Insertar OK", res.text, "success")
        except Exception as e:
            return self._display_notification("Error conexión Insertar", str(e), "danger")

    def action_test_lectura_connection(self):
        if not self.kardex_url_lectura:
            raise UserError("Falta la URL de lectura configurada.")

        messages = []
        for tipo in [1, 2]:
            estado = 2
            full_url = f"{self.kardex_url_lectura}/status/{estado}/{tipo}"
            try:
                res = requests.get(full_url, timeout=10)
                res.raise_for_status()
                messages.append(f"✅ Tipo {tipo}: Conexión exitosa")
            except Exception as e:
                messages.append(f"❌ Tipo {tipo}: Error - {str(e)}")

        return self._display_notification("Resultado de prueba de lectura", "\n".join(messages), "info")

        
    def test_kardex_update(self):
        self.ensure_one()
        if not self.kardex_url_update:
            raise UserError("⚠️ Debe configurar la URL de actualización para Kardex.")

        try:
            payload = {
                "identificador": 1396534  # Valor de prueba
            }
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.kardex_url_update, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return self._display_notification("Conexión Actualización OK", response.text, "success")
        except Exception as e:
            return self._display_notification("Error conexión Actualización", str(e), "danger")

    def _display_notification(self, title, message, type="info"):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': type,
                'sticky': True,
            }
        }
