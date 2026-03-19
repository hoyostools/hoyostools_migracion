from datetime import date
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    fecha_activacion = date(2026, 3, 4)

    cantidad_maxima_cajas = fields.Integer(
        string='Cantidad Máxima de Cajas',
        compute='_compute_from_sale',
        store=False,
        precompute=False,
        readonly=True
    )

    valor_caja = fields.Float(
        string='Valor Caja',
        compute='_compute_from_sale',
        precompute=False,
        store=False,
        readonly=True
    )

    total_flete = fields.Float(
        string='Total Flete',
        compute='_compute_from_sale',
        precompute=False,
        store=False,
        readonly=True
    )

    cajas_usadas = fields.Integer(
        string='Cajas Usadas',
        # compute='_compute_cajas_usadas',
        store=False,
        precompute=False
    )

    ahorro = fields.Float(
        string='Ahorro',
        compute='_compute_ahorro',
        store=False,
        precompute=False
    )

    # -------------------------------------------------------
    # Traer datos desde Sale Order
    # -------------------------------------------------------

    @api.depends('sale_id.cantidad_maxima_cajas','sale_id.valor_caja','sale_id.total_flete')
    def _compute_from_sale(self):
        for picking in self:
            sale = picking.sale_id

            if sale:
                picking.cantidad_maxima_cajas = sale.cantidad_maxima_cajas
                picking.valor_caja = sale.valor_caja
                picking.total_flete = sale.total_flete
            else:
                picking.cantidad_maxima_cajas = 0
                picking.valor_caja = 0.0
                picking.total_flete = 0.0

    # -------------------------------------------------------
    # Calcular cajas usadas
    # -------------------------------------------------------

    # @api.depends('state', 'name', 'move_line_ids.result_package_id')
    # def _compute_cajas_usadas(self):
    #     for picking in self:

    #         if picking.state == 'done' and 'PACK' in (picking.name or ''):
    #             paquetes = picking.move_line_ids.mapped('result_package_id')
    #             picking.cajas_usadas = len(paquetes.filtered(lambda p: p))
    #         else:
    #             picking.cajas_usadas = 0

    # -------------------------------------------------------
    # Calcular ahorro
    # -------------------------------------------------------

    @api.depends('cajas_usadas', 'valor_caja', 'total_flete')
    def _compute_ahorro(self):
        for picking in self:

            picking.ahorro = (
                picking.total_flete - (picking.cajas_usadas * picking.valor_caja)
            )
