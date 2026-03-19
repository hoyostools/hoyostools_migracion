# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = "product.product"

    total_value = fields.Monetary(
        string="Total Value",
        compute='_compute_value_svl',
        precompute=True,
        store=True,
        index=True,
        compute_sudo=True,
        currency_field='company_currency_id'
    )
    proyeccion_inventario = fields.Float(
        string='Proy. Inventario',
        # compute='calcular_proyeccion_inventario',
        precompute=True,
        store=True,
        index=True,
        compute_sudo=True,
    )
    inventory_projection = fields.Char(compute="_compute_inventory_projection", string="Proyección inventario")

    @api.depends('orderpoint_ids.inventory_projection')
    def _compute_inventory_projection(self):
        # Toma el registro más reciente modificado, o si no hay ninguno modificado, busca el más reciente creado
        for record in self:
            if any(o.last_update_inv_proj for o in record.orderpoint_ids):
                valid_orderpoints = record.orderpoint_ids.filtered(lambda r: r.last_update_inv_proj)
                sorted_orderpoints = valid_orderpoints.sorted(key=lambda r: r.last_update_inv_proj, reverse=True)
            else:
                sorted_orderpoints = record.orderpoint_ids.sorted(key=lambda r: r.create_date, reverse=True)

            if sorted_orderpoints:
                record.inventory_projection = sorted_orderpoints[0].inventory_projection
            else:
                record.inventory_projection = 'Cantidad Paca No Definida'

    # @api.depends('free_qty','promedio_consumo')
    # @api.depends_context('free_qty','promedio_consumo')
    def calcular_proyeccion_inventario(self):
        for record in self:
            # Calcular el proyeccion_inventario del producto
            record.proyeccion_inventario = (record.free_qty / record.promedio_consumo) if record.promedio_consumo != 0 else 0
            # Actualizar el inventory_projection de warehouse
            for swo in record.orderpoint_ids:
                if swo.promedio_consumo:
                    swo.inventory_projection = str(round(swo.qty_forecast / swo.promedio_consumo, 3)
                                                   ) if swo.promedio_consumo != 0 else '0'
                else:
                    swo.inventory_projection = 'Cantidad Paca No Definida'

    responsible_id = fields.Many2one("res.users", related="product_tmpl_id.responsible_id", string="Responsable", store=True)
