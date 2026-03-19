from odoo import models, fields, _
from odoo.exceptions import UserError
import xmlrpc.client

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_synced = fields.Boolean(string="Sincronizado", readonly=True, copy=False)
    meli_tracking_pdf = fields.Binary(
        string="Guía Meli (PDF)",
        attachment=True,
    )
    meli_tracking_filename = fields.Char(string="Nombre del archivo")


    def action_sync_order(self):
        for order in self:
            if order.is_synced:
                raise UserError(_('Este pedido ya fue sincronizado.'))

            # Obtener parámetros de conexión
            config = self.env['ir.config_parameter'].sudo()
            url = config.get_param('sync_odoo_xmlrpc.remote_odoo_url')
            db = config.get_param('sync_odoo_xmlrpc.remote_odoo_db')
            user = config.get_param('sync_odoo_xmlrpc.remote_odoo_user')
            password = config.get_param('sync_odoo_xmlrpc.remote_odoo_password')

            if not all([url, db, user, password]):
                raise UserError(_('Debe configurar la URL, base de datos, usuario y contraseña en Ajustes.'))

            try:
                # Autenticación en remoto
                common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
                uid = common.authenticate(db, user, password, {})
                if not uid:
                    raise UserError(_('Autenticación fallida. Verifique credenciales.'))

                models_rpc = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

                # Tomar el partner de la compañía
                company_partner = order.company_id.partner_id
                if not company_partner:
                    raise UserError(_('La compañía del pedido no tiene un partner asignado.'))

                # Buscar partner de la compañía en la base remota
                # partner_domain = [('vat', '=', company_partner.vat)] if company_partner.vat else [('name', '=', company_partner.name)]
                partner_domain = ['|', ('vat', '=', company_partner.vat), ('name', '=', company_partner.name)]
                partner_ids = models_rpc.execute_kw(db, uid, password, 'res.partner', 'search', [partner_domain], {'limit': 1})

                if partner_ids:
                    remote_partner_id = partner_ids[0]
                else:
                    remote_partner_id = models_rpc.execute_kw(db, uid, password, 'res.partner', 'create', [{
                        'name': company_partner.name,
                        'vat': company_partner.vat,
                        'street': company_partner.street,
                        'phone': company_partner.phone,
                        'email': company_partner.email,
                    }])

                # Construir líneas del pedido
                remote_lines = []
                for line in order.order_line:
                    if not line.product_id.default_code:
                        raise UserError(_(f'El producto "{line.product_id.display_name}" no tiene código interno (default_code)'))

                    # Buscar producto en remoto
                    prod_ids = models_rpc.execute_kw(
                        db, uid, password, 'product.product', 'search',
                        [[('default_code', '=', line.product_id.default_code)]],
                        {'limit': 1}
                    )

                    if prod_ids:
                        remote_prod_id = prod_ids[0]
                        # Agregar la línea solo si el producto existe en remoto
                        remote_lines.append((0, 0, {
                            'product_id': remote_prod_id,
                            'product_uom_qty': line.product_uom_qty,
                            # 'price_unit': line.price_unit,
                            'name': line.name,
                        }))
                    # Si no existe el producto, se omite la línea

                if not remote_lines:
                    raise UserError(_('Ninguna línea pudo sincronizarse porque los productos no existen en la base destino.'))

                remote_campaign_id = False
                if order.campaign_id:
                    # Buscar campaña por nombre
                    campaign_ids = models_rpc.execute_kw(
                        db, uid, password,
                        'utm.campaign', 'search',
                        [[('name', '=', order.campaign_id.name)]],
                        {'limit': 1}
                    )
                    if campaign_ids:
                        remote_campaign_id = campaign_ids[0]
                    else:
                        # Crear campaña si no existe
                        remote_campaign_id = models_rpc.execute_kw(
                            db, uid, password,
                            'utm.campaign', 'create',
                            [{
                                'name': order.campaign_id.name,
                            }]
                        )
                        
                remote_origin = False
                if order.origin:
                    remote_origin = order.origin
                
                # Datos del pedido a crear en remoto
                order_data = {
                    'partner_id': remote_partner_id,  # Siempre el partner de la compañía
                    'origin': remote_origin,
                    'date_order': str(order.date_order),
                    'order_line': remote_lines,
                }
                # ✅ Validar que el archivo esté presente y tenga nombre antes de enviarlo
                if order.meli_tracking_pdf and order.meli_tracking_filename:
                    order_data['meli_tracking_pdf'] = order.meli_tracking_pdf
                    order_data['meli_tracking_filename'] = order.meli_tracking_filename
                    
                if remote_campaign_id:
                    order_data['campaign_id'] = remote_campaign_id

                # Crear pedido en remoto
                remote_order_id = models_rpc.execute_kw(db, uid, password, 'sale.order', 'create', [order_data])

                # Marcar pedido como sincronizado
                order.is_synced = True

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sincronización exitosa'),
                        'message': f'Pedido creado en remoto con ID {remote_order_id}',
                        'sticky': False,
                        'type': 'success',
                    }
                }

            except Exception as e:
                raise UserError(_('Error al sincronizar con la base remota: %s') % str(e))

