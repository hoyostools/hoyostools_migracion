import math
from datetime import date
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    fecha_activacion = date(2026, 3, 4)

    ciudad_principal = fields.Boolean(
        string='Ciudad Principal',
        compute='_compute_ciudad_principal',
        precompute=False
    )

    valor_caja = fields.Float(
        string='Valor Caja',
        compute='_compute_valor_caja',
        precompute=False
    )

    cantidad_maxima_cajas = fields.Integer(
        string='Cantidad Máxima de Cajas',
        compute='_compute_cantidad_maxima_cajas',
        precompute=False
    )

    total_flete = fields.Float(
        string='Total Flete',
        compute='_compute_flete_fields',
        precompute=False
    )

    porcentaje_flete = fields.Float(
        string='% Flete',
        compute='_compute_flete_fields',
        precompute=False
    )

    # -------------------------------------------------------
    # Ciudad principal
    # -------------------------------------------------------

    @api.depends('partner_shipping_id.city_id')
    def _compute_ciudad_principal(self):
        for order in self:
            if order.create_date and order.create_date.date() < self.fecha_activacion:
                order.ciudad_principal = False
                continue

            city = order.partner_shipping_id.city_id
            order.ciudad_principal = city.ciudad_principal if city else False

    # -------------------------------------------------------
    # Valor caja
    # -------------------------------------------------------

    @api.depends('partner_shipping_id.city_id')
    def _compute_valor_caja(self):
        for order in self:
            if order.create_date and order.create_date.date() < self.fecha_activacion:
                order.valor_caja = 0.0
                continue

            city = order.partner_shipping_id.city_id
            order.valor_caja = city.valor_caja if city else 0.0

    # -------------------------------------------------------
    # Cantidad máxima de cajas
    # -------------------------------------------------------

    @api.depends('amount_untaxed', 'valor_caja', 'ciudad_principal')
    def _compute_cantidad_maxima_cajas(self):

        config = self.env['ir.config_parameter'].sudo()

        porcentaje_regional = float(
            config.get_param(
                'costos_transportadora.presupuesto_transportadora_regional',
                default=0.0
            )
        ) / 100.0

        porcentaje_principal = float(
            config.get_param(
                'costos_transportadora.presupuesto_transportadora_principal',
                default=0.0
            )
        ) / 100.0

        for order in self:

            # 🔴 No calcular histórico
            if order.create_date and order.create_date.date() < self.fecha_activacion:
                order.cantidad_maxima_cajas = 0
                continue

            porcentaje = (
                porcentaje_principal
                if order.ciudad_principal
                else porcentaje_regional
            )

            if order.valor_caja:
                order.cantidad_maxima_cajas = math.ceil(
                    (order.amount_untaxed * porcentaje) / order.valor_caja
                )
            else:
                order.cantidad_maxima_cajas = 0

    # -------------------------------------------------------
    # Total flete y % flete
    # -------------------------------------------------------

    @api.depends('valor_caja', 'cantidad_maxima_cajas', 'amount_untaxed')
    def _compute_flete_fields(self):
        for order in self:

            # 🔴 No calcular histórico
            if order.create_date and order.create_date.date() < self.fecha_activacion:
                order.total_flete = 0.0
                order.porcentaje_flete = 0.0
                continue

            order.total_flete = (
                order.valor_caja * order.cantidad_maxima_cajas
            )

            if order.amount_untaxed:
                porcentaje = (
                    order.total_flete / order.amount_untaxed
                ) * 100

                order.porcentaje_flete = round(porcentaje, 2)
            else:
                order.porcentaje_flete = 0.0
