from odoo import http
from odoo.http import request
from werkzeug.utils import redirect
from datetime import datetime, timedelta
import requests

class PortalSaleTracking(http.Controller):

    # carriers permitidos
    VALID_CARRIERS = [80,128,129,130,131,132,133,140,183,1]

    @http.route('/order/tracking/validate', type='http', auth='public', website=True, csrf=False)
    def validate_captcha(self, **post):

        recaptcha_response = post.get('g-recaptcha-response')

        config = request.env['ir.config_parameter'].sudo()

        secret = config.get_param('recaptcha_private_key')
        min_score = float(config.get_param('recaptcha_min_score', 0.7))

        result = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={
                'secret': secret,
                'response': recaptcha_response
            }
        ).json()

        success = result.get('success')
        score = result.get('score', 0)

        if success and score >= min_score:
            request.session['tracking_consultas'] = 0
            return request.redirect('/order/tracking')

        return request.render(
            'sale_order_tracking_portal.tracking_page',
            {'error': 'No se pudo verificar que no eres un robot'}
        )

    # ---------------------------------------------------------
    # Página principal
    # ---------------------------------------------------------
    @http.route('/order/tracking', type='http', auth='public', website=True)
    def order_tracking_page(self, **kwargs):
        return request.render(
            'sale_order_tracking_portal.tracking_page',
            {}
        )

    # ---------------------------------------------------------
    # Buscar por orden
    # ---------------------------------------------------------
    @http.route('/order/tracking/search', type='http', auth='public', website=True, methods=['POST'])
    def order_tracking_search(self, **post):

        # contador en sesión
        consultas = request.session.get('tracking_consultas', 0)
        consultas += 1
        request.session['tracking_consultas'] = consultas
        config = request.env['ir.config_parameter'].sudo()

        site_key = config.get_param('recaptcha_public_key')
        secret_key = config.get_param('recaptcha_private_key')
        min_score = float(config.get_param('recaptcha_min_score', 0.7))

        # cada 5 consultas pedir captcha
        if consultas % 5 == 0:
            return request.render(
                'sale_order_tracking_portal.captcha_template',
                {
                   'site_key': site_key
                }
            )

        order_name = post.get('order_name', '').strip().upper()

        sale_order = request.env['sale.order'].sudo().search([
            ('name', '=', order_name)
        ], limit=1)

        if not sale_order:
            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {'error': 'La orden no existe'}
            )

        # validar método de envío
        if sale_order.carrier_id.id not in self.VALID_CARRIERS:
            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {'error': 'Lo siento tu pedido no aplica para Rastreo por el metodo de envio de la orden'}
            )

        guia = sale_order.guia_url

        # pedido sin guía
        if not guia or guia.strip().lower() == 'url guia':
            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {'error': 'Lo sentimos tu pedido aun esta en proceso logistico'}
            )

        # transportadora
        if guia.startswith('https'):
            return redirect(guia)

        # camiones propios
        return request.render(
            'sale_order_tracking_portal.tracking_page',
            {
                'camion_propio': True,
                'placa': guia
            }
        )

    # ---------------------------------------------------------
    # Buscar por NIT
    # ---------------------------------------------------------
    @http.route('/order/tracking/nit', type='http', auth='public', website=True, methods=['POST'])
    def order_tracking_nit(self, **post):

        nit = post.get('nit')

        partner = request.env['res.partner'].sudo().search([
            ('vat', 'ilike', nit)
        ], limit=1)

        if not partner:
            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {'error': 'No encontramos clientes con ese NIT'}
            )

        today = datetime.today()
        three_days = today - timedelta(days=3)

        orders = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('date_order', '>=', three_days),
            ('carrier_id', 'in', self.VALID_CARRIERS)
        ], order="date_order desc")

        if not orders:
            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {'error': 'No hay órdenes disponibles para rastreo'}
            )

        return request.render(
            'sale_order_tracking_portal.tracking_orders_list',
            {'orders': orders}
        )

    # ---------------------------------------------------------
    # Abrir orden desde lista
    # ---------------------------------------------------------
    @http.route('/order/tracking/direct/<int:order_id>', type='http', auth='public', website=True)
    def order_tracking_direct(self, order_id):

        order = request.env['sale.order'].sudo().browse(order_id)

        if not order.exists():
            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {'error': 'La orden no existe'}
            )

        if order.carrier_id.id not in self.VALID_CARRIERS:
            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {'error': 'Lo siento tu pedido no aplica para Rastreo por el metodo de envio de la orden'}
            )

        guia = order.guia_url

        if not guia or guia.strip().lower() == 'url guia':
            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {'error': 'Lo sentimos tu pedido aun esta en proceso logistico'}
            )

        if guia.startswith('https'):
            return redirect(guia)

        return request.render(
            'sale_order_tracking_portal.tracking_page',
            {
                'camion_propio': True,
                'placa': guia
            }
        )