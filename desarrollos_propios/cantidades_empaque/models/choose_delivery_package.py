# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = 'choose.delivery.package'

    cajas_a_usar = fields.Integer(string='Cajas a usar:')
    cantidad_maxima_cajas = fields.Integer(string='Cantidad Máxima de Cajas:', related='picking_id.cantidad_maxima_cajas')
    
    packaging_order_observation = fields.Char(
        string="Totalidad del empaque de la orden",
        related='picking_id.sale_id.packaging_order_observation',
        readonly=False,
    )

    def action_put_in_pack(self):
        self = self.with_context(cajas_a_usar=self.cajas_a_usar)
        self.picking_id.cajas_usadas = self.cajas_a_usar
        return super().action_put_in_pack()

    # @api.constrains('cajas_a_usar', 'cantidad_maxima_cajas')
    # def _check_cajas(self):
    #     for record in self:
    #         if record.cajas_a_usar > record.cantidad_maxima_cajas:
    #             raise ValidationError(
    #                 f"No puedes usar más de {record.cantidad_maxima_cajas} cajas."
    #             )



