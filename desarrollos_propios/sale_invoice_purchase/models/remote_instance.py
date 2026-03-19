import xmlrpc.client
from odoo import models, fields, _, api


class RemoteInstance(models.Model):
    _name = "remote.instance"
    _description = 'Instancia Remota Odoo para Sincronización'

    name = fields.Char("Nombre", required=True)
    url = fields.Char("URL del Servidor", required=True)
    db = fields.Char("Base de Datos", required=True)
    username = fields.Char("Usuario", required=True)
    password = fields.Char("Contraseña", required=True)

    def action_test_connection(self):
        """
        Botón que permite probar la conexión con la instancia remota Odoo vía XML-RPC.
        """
        for rec in self:
            try:
                common = xmlrpc.client.ServerProxy(f"{rec.url}/xmlrpc/2/common")
                uid = common.authenticate(rec.db, rec.username, rec.password, {})
                if not uid:
                    raise Exception(_("No se pudo autenticar con las credenciales proporcionadas."))

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Conexión exitosa'),
                        'message': _('La conexión con la instancia remota fue exitosa.'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            except Exception as e:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error de conexión'),
                        'message': str(e),
                        'type': 'danger',
                        'sticky': True,
                    }
                }
