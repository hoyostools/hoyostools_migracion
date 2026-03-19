from odoo import models, fields, _
from odoo.exceptions import UserError
import xmlrpc.client

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_purchase_sync = fields.Boolean(string="Sincronizar al confirmar compra", config_parameter='purchase_to_sale_sync.enable_purchase_sync')
    remote_odoo_url = fields.Char(string="URL de Odoo remoto")
    remote_odoo_db = fields.Char(string="Base de datos remota")
    remote_odoo_user = fields.Char(string="Usuario remoto")
    remote_odoo_password = fields.Char(string="Contraseña remota")

    def set_values(self):
        super().set_values()
        config = self.env['ir.config_parameter'].sudo()
        config.set_param('purchase_to_sale_sync.remote_odoo_url', self.remote_odoo_url)
        config.set_param('purchase_to_sale_sync.remote_odoo_db', self.remote_odoo_db)
        config.set_param('purchase_to_sale_sync.remote_odoo_user', self.remote_odoo_user)
        config.set_param('purchase_to_sale_sync.remote_odoo_password', self.remote_odoo_password)

    def get_values(self):
        res = super().get_values()
        config = self.env['ir.config_parameter'].sudo()
        res.update({
            'remote_odoo_url': config.get_param('purchase_to_sale_sync.remote_odoo_url'),
            'remote_odoo_db': config.get_param('purchase_to_sale_sync.remote_odoo_db'),
            'remote_odoo_user': config.get_param('purchase_to_sale_sync.remote_odoo_user'),
            'remote_odoo_password': config.get_param('purchase_to_sale_sync.remote_odoo_password'),
        })
        return res

    def action_test_connection(self):
        config = self.env['ir.config_parameter'].sudo()
        url = config.get_param('purchase_to_sale_sync.remote_odoo_url')
        db = config.get_param('purchase_to_sale_sync.remote_odoo_db')
        user = config.get_param('purchase_to_sale_sync.remote_odoo_user')
        password = config.get_param('purchase_to_sale_sync.remote_odoo_password')

        if not all([url, db, user, password]):
            raise UserError(_('Debe configurar la URL, base de datos, usuario y contraseña en la configuración.'))

        try:
            common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
            uid = common.authenticate(db, user, password, {})
            if not uid:
                raise UserError(_('Autenticación fallida. Verifique credenciales.'))

            version = common.version()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Conexión exitosa'),
                    'message': f"Conectado a {version.get('server_version', '')}",
                    'sticky': False,
                    'type': 'success',
                }
            }

        except Exception as e:
            raise UserError(_('Error al conectar con la base remota: %s') % str(e))
