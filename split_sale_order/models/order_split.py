from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LimitConfigCompany(models.Model):
    _inherit = "res.company"

    max_lines_per_order = fields.Integer(string="Máxima cantidad de líneas por cotización", default=50, readonly=False)
    split_activated = fields.Boolean(string="División de órdenes de venta", default=False, readonly=False)


class LimitConfig(models.TransientModel):
    _inherit = "res.config.settings"

    max_lines_per_order = fields.Integer(string="Máxima cantidad de líneas por cotización",
                                         related="company_id.max_lines_per_order", readonly=False)
    split_activated = fields.Boolean(string="División de órdenes de venta", related="company_id.split_activated",
                                     readonly=False)

    @api.onchange('max_lines_per_order')
    def restriction_max_lines_per_order(self):
        if self.split_activated:
            if self.max_lines_per_order <= 0:
                raise UserError("Error: El valor máximo de cantidad de lineas por cotización debe ser mayor a 0")


class SplitOrder(models.Model):
    _inherit = 'sale.order'

    is_split_order = fields.Boolean(default=False)
    origin_order_name = fields.Char()
    seq_split_order = fields.Integer()

    def action_confirm(self):
        for order in self:
            if order.detect_exceptions():
                return order._popup_exceptions()
            if not order.carrier_id:
                raise UserError("Error: Falta definir método de envío para: " + order.display_name)
        if self.env.company.split_activated:
            for order in self:
                list_lines_per_order = order.necessary_orders()
                if list_lines_per_order and not order.is_split_order and order.payment_term_id.name.lower() != 'pago inmediato' and order.carrier_id.split_active and order.warehouse_id.code == "CLH" and not self.detect_exceptions() and not order.b4b and not order.servicio_logistico:
                    new_orders = []
                    seq_name = 1
                    for qty in list_lines_per_order:
                        new_orders.append(order.copy({'is_split_order': True, 'origin_order_name': order.display_name,
                                                      'seq_split_order': seq_name, 'order_line': False}))
                        new_orders[-1].order_line = False
                        new_orders[-1].order_line = order.order_line[:qty]
                        new_orders[-1].carrier_id = order.carrier_id
                        seq_name += 1
                    order.message_post(body="Se ha realizado una división en " + str(
                        len(list_lines_per_order)) + " de la presente cotización para facilitar su manejo.")
                    for new_order in new_orders:
                        new_order.action_sale_ok()
                        remittance_link = f'<a href="/web#id={new_order.id}&model=sale.order&view_type=form">{new_order.name}</a>'
                        order.message_post(body=f"Cotización generada: {remittance_link}", message_type='comment',
                                           body_is_html=True)

                        remittance_link_self = f'<a href="/web#id={order.id}&model=sale.order&view_type=form">{order.name}</a>'
                        new_order.message_post(
                            body=f"Cotización generada a partir de la división de: {remittance_link_self}",
                            message_type='comment',
                            body_is_html=True)

                    order.write({"state": "cancel"})
                    order.picking_ids = False
                    return True
        return super(SplitOrder, self).action_confirm()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _("New")) == _("New") and vals.get('is_split_order'):
                vals['name'] = vals.get('origin_order_name') + '-' + str(vals.get('seq_split_order'))
        return super().create(vals_list)

    def necessary_orders(self):
        max_lines_per_order = self.env.company.max_lines_per_order
        line_qty = len(self.order_line)
        orders_needed = line_qty // max_lines_per_order
        residue = line_qty % max_lines_per_order
        if orders_needed < 2:
            return False
        else:
            lines_per_order = line_qty // orders_needed
            list_lines_per_order = [lines_per_order] * orders_needed
            list_lines_per_order[-1] += residue
            return list_lines_per_order


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    split_active = fields.Boolean(string="División de órdenes de venta", default=False)