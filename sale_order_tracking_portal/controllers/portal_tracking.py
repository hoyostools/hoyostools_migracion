from odoo import http
from odoo.http import request
from werkzeug.utils import redirect
from datetime import datetime, timedelta
import requests
import logging

_logger = logging.getLogger(__name__)


class PortalSaleTracking(http.Controller):

    VALID_CARRIERS = [80,128,129,130,131,132,133,140,183,1]

    # ---------------------------------------------------------
    # VALIDAR RECAPTCHA
    # ---------------------------------------------------------
    def _verify_recaptcha(self, token):

        config = request.env['ir.config_parameter'].sudo()

        secret_key = config.get_param('recaptcha_private_key')
        min_score = float(config.get_param('recaptcha_min_score', 0.7))

        if not token:
            _logger.warning("Token recaptcha vacío")
            return False

        if not secret_key:
            _logger.warning("Secret key recaptcha no configurada")
            return False

        try:

            result = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={
                    "secret": secret_key,
                    "response": token,
                },
                timeout=5
            ).json()

        except Exception as e:
            _logger.error("Error conectando con reCAPTCHA: %s", e)
            return False

        _logger.info("Respuesta recaptcha: %s", result)

        success = result.get("success")
        score = result.get("score", 0)
        action = result.get("action")

        if not success:
            return False

        if score < min_score:
            _logger.warning("Score bajo detectado: %s", score)
            return False

        if action != "tracking":
            _logger.warning("Acción recaptcha inválida: %s", action)
            return False

        return True


    # ---------------------------------------------------------
    # PAGINA PRINCIPAL
    # ---------------------------------------------------------
    @http.route('/order/tracking', type='http', auth='public', website=True)
    def order_tracking_page(self, **kwargs):

        config = request.env['ir.config_parameter'].sudo()
        site_key = config.get_param('recaptcha_public_key')

        # reiniciar contador
        request.session['tracking_consultas'] = 0

        return request.render(
            'sale_order_tracking_portal.tracking_page',
            {
                'site_key': site_key,
            }
        )


    # ---------------------------------------------------------
    # BUSCAR POR ORDEN
    # ---------------------------------------------------------
    @http.route('/order/tracking/search', type='http', auth='public', website=True, methods=['POST'])
    def order_tracking_search(self, **post):

        consultas = request.session.get('tracking_consultas', 0) + 1
        request.session['tracking_consultas'] = consultas

        config = request.env['ir.config_parameter'].sudo()
        site_key = config.get_param('recaptcha_public_key')

        # activar captcha desde la consulta 5
        if consultas >= 5:

            token = post.get('recaptcha_token')

            if not self._verify_recaptcha(token):

                return request.render(
                    'sale_order_tracking_portal.tracking_page',
                    {
                        'error': 'Por seguridad debes validar el captcha',
                        'site_key': site_key,
                    }
                )

        order_name = post.get('order_name', '').strip().upper()

        sale_order = request.env['sale.order'].sudo().search([
            ('name', '=', order_name)
        ], limit=1)

        if not sale_order:

            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {
                    'error': 'La orden no existe',
                    'site_key': site_key
                }
            )

        if sale_order.carrier_id.id not in self.VALID_CARRIERS:

            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {
                    'error': 'Lo siento tu pedido no aplica para rastreo por el método de envío',
                    'site_key': site_key
                }
            )

        guia = sale_order.guia_url

        if not guia or guia.strip().lower() == 'url guia':

            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {
                    'error': 'Lo sentimos tu pedido aún está en proceso logístico',
                    'site_key': site_key
                }
            )

        if guia.startswith('https'):
            return redirect(guia)

        return request.render(
            'sale_order_tracking_portal.tracking_page',
            {
                'site_key': site_key,
                'camion_propio': True,
                'placa': guia
            }
        )


    # ---------------------------------------------------------
    # BUSCAR POR NIT
    # ---------------------------------------------------------
    @http.route('/order/tracking/nit', type='http', auth='public', website=True, methods=['POST'])
    def order_tracking_nit(self, **post):

        nit = post.get('nit')

        config = request.env['ir.config_parameter'].sudo()
        site_key = config.get_param('recaptcha_public_key')

        partner = request.env['res.partner'].sudo().search([
            ('vat', 'ilike', nit)
        ], limit=1)

        if not partner:

            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {
                    'error': 'No encontramos clientes con ese NIT',
                    'site_key': site_key
                }
            )

        today = datetime.today()
        ten_days = today - timedelta(days=10)

        orders = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('date_order', '>=', ten_days),
            ('carrier_id', 'in', self.VALID_CARRIERS)
        ], order="date_order desc")

        if not orders:

            return request.render(
                'sale_order_tracking_portal.tracking_page',
                {
                    'error': 'No hay órdenes disponibles para rastreo',
                    'site_key': site_key
                }
            )

        return request.render(
            'sale_order_tracking_portal.tracking_orders_list',
            {
                'orders': orders
            }
        )