from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def obtener_paquete(self):
        if self.move_ids:
            move_lines = self.move_ids.move_line_ids.filtered(lambda ml: ml.result_package_id)
            if move_lines:
                return move_lines[0].result_package_id.name
        return False

    def obtener_tipo_empaque(self):
        if self.move_ids:
            move_lines = self.move_ids.move_line_ids.filtered(lambda ml: ml.result_package_id)
            if move_lines:
                return move_lines[0].result_package_id.package_type_id.name
        return False

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def obtener_observaciones_empaque(self):
        for order in self:
            pickings = order.picking_ids.filtered(
                lambda pick: pick.picking_type_id.id == order.warehouse_id.out_type_id.id).mapped(
                'packaging_order_observation')
            if pickings:
                try:
                    return ', '.join(pickings)
                except:
                    return False
            return False

    def print_report_servicio_logistico(self):
        for order in self:
            # Verificar si al menos uno de los campos es True
            if not order.b4b and not order.servicio_logistico:
                raise UserError("El reporte solo puede imprimirse cuando la orden es 'B4B' o 'Servicio Logístico'.")

            # Validar que la orden de entrega esté realizada o por realizar
            picking_states = order.picking_ids.filtered(lambda pick: pick.picking_type_id.id == order.warehouse_id.out_type_id.id).mapped('state')
            if not any(state in ['done', 'confirmed', 'assigned'] for state in picking_states):
                raise UserError(
                    "El reporte solo puede imprimirse cuando la orden de entrega está realizada o por realizar.")

            # # Validar que la venta ya esté facturada
            # if not order.invoice_ids.filtered(lambda inv: inv.state == 'posted'):
            #     raise UserError("El reporte solo puede imprimirse cuando la venta está facturada.")

        # Si pasa la validación, continuar con la impresión del reporte
        return self.sudo().env.ref('reporte_servicio_logistico.report_servicio_logistico').report_action(self)

