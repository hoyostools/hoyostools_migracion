# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class UpdatePaymentMethodWizard(models.TransientModel):
    _name = "update.payment.method.wizard"
    _description = "Update Payment Method Wizard"

    pos_payment_id = fields.Many2one('pos.payment', string="Pago", readonly=True)
    payment_method_ids = fields.Many2many('pos.payment.method', compute='_compute_pos_payment_methods_ids', string="Métodos de Pago Disponibles")
    payment_method_id = fields.Many2one('pos.payment.method', string="Nuevo Método de Pago", required=True)

    def _compute_pos_payment_methods_ids(self):
        for wizard in self:
            wizard.payment_method_ids = wizard.pos_payment_id.session_id.config_id.payment_method_ids.ids

    @api.model
    def default_get(self, fields):
        res = super(UpdatePaymentMethodWizard, self).default_get(fields)
        payment = self.env['pos.payment'].browse(self.env.context.get('active_id'))
        res['payment_method_ids'] = payment.session_id.config_id.payment_method_ids
        return res

    def update_payment_method(self):
        if self.pos_payment_id and self.payment_method_id:
            order = self.pos_payment_id.pos_order_id
            session = order.session_id

            if session.state != 'opened':
                raise ValidationError(_('La sesión del punto de venta debe estar "Abierta" para modificar el método de pago del pedido %s.') % order.name)

            if self.payment_method_id.split_transactions and not order.partner_id:
                raise ValidationError(_(
                    'Ha habilitado la opción "Identificar Cliente" para este método de pago, '
                    'pero el pedido %s no tiene un cliente asignado.'
                ) % order.name)

            self.pos_payment_id.sudo().write({
                'payment_method_id': self.payment_method_id.id
            })

