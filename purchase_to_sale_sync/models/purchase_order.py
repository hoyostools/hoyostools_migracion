from odoo import models, fields, api, _
import xmlrpc.client
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    sincronizated = fields.Boolean(string="Sincronizada?",readonly="1")

    def button_confirm(self):
        result = super().button_confirm()
        logging.info('************* CONFIRMAR **************************')
        # Verifica si la sincronización está activada
        enable_sync = self.env['ir.config_parameter'].sudo().get_param('purchase_to_sale_sync.enable_purchase_sync')
        if enable_sync and enable_sync.lower() in ['1', 'true', 'yes']:
            logging.info('**************** SINCRONIZACIÓN ACTIVA *******************')
            for order in self:
                order._sync_sale_order_to_remote()

        return result

    def _sync_sale_order_to_remote(self):
        config = self.env['ir.config_parameter'].sudo()
        remote_url = config.get_param('purchase_to_sale_sync.remote_odoo_url')
        remote_db = config.get_param('purchase_to_sale_sync.remote_odoo_db')
        remote_user = config.get_param('purchase_to_sale_sync.remote_odoo_user')
        remote_password = config.get_param('purchase_to_sale_sync.remote_odoo_password')

        if not all([remote_url, remote_db, remote_user, remote_password]):
            _logger.warning("Faltan datos de configuración para sincronizar con Odoo remoto.")
            return

        for order in self:
            try:
                # Conexión XML-RPC
                common = xmlrpc.client.ServerProxy(f'{remote_url}/xmlrpc/2/common')
                uid = common.authenticate(remote_db, remote_user, remote_password, {})
                models = xmlrpc.client.ServerProxy(f'{remote_url}/xmlrpc/2/object')

                # Buscar o crear el cliente
                partner_name = order.partner_id.name
                partner_id = models.execute_kw(
                    remote_db, uid, remote_password,
                    'res.partner', 'search',
                    [[['name', '=', partner_name]]], {'limit': 1}
                )
                if not partner_id:
                    partner_id = models.execute_kw(
                        remote_db, uid, remote_password,
                        'res.partner', 'create',
                        [{
                            'name': partner_name,
                            'email': order.partner_id.email or '',
                        }]
                    )
                else:
                    partner_id = partner_id[0]

                # Preparar líneas de venta
                sale_lines = []
                for line in order.order_line:
                    default_code = line.product_id.default_code
                    if not default_code:
                        continue

                    product_remote_ids = models.execute_kw(
                        remote_db, uid, remote_password,
                        'product.product', 'search',
                        [[['default_code', '=', default_code]]], {'limit': 1}
                    )
                    if not product_remote_ids:
                        _logger.warning(f"Producto con default_code '{default_code}' no encontrado en instancia remota.")
                        continue

                    sale_lines.append((0, 0, {
                        'product_id': product_remote_ids[0],
                        'product_uom_qty': line.product_qty,
                        'price_unit': line.price_unit,
                        'name': line.name or default_code,
                    }))

                if not sale_lines:
                    _logger.warning(f"No se pudieron agregar líneas de venta para la orden {order.name}")
                    return

                # Crear la orden de venta
                models.execute_kw(
                    remote_db, uid, remote_password,
                    'sale.order', 'create',
                    [{
                        'partner_id': partner_id,
                        'order_line': sale_lines,
                        'client_order_ref': order.name,
                        'note': 'Generado automáticamente desde orden de compra de Odoo origen.'
                    }]
                )
                logging.info('************ ORDEN DE VENTA CREADA **********************')
                self.write({'sincronizated': True})

            except Exception as e:
                _logger.error(f"Error al sincronizar orden de compra {order.name} con Odoo remoto: {e}")
