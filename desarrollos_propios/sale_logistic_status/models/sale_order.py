from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    logistic_state = fields.Selection(
        [
            ('pending', 'Pendiente por Separar'),
            ('processing', 'En Proceso de Separado'),
            ('packing', 'En Empaque'),
            ('shipping', 'Empacado'),
            ('done', 'Despachado'),
        ],
        string="Estado Logístico",
        compute="_compute_logistic_state",
        store=True,
    )

    @api.depends(
        'state',
        'procesada',
        'picking_ids.state',
        'picking_ids.name',
        'picking_ids.backorder_id',
    )
    def _compute_logistic_state(self):
        for order in self:

            # Si no está confirmada
            if order.state != 'sale':
                order.logistic_state = False
                continue

            # Excluir cancelados y backorders
            pickings = order.picking_ids.filtered(
                lambda p: p.state != 'cancel' and not p.backorder_id
            )

            pick_pickings = pickings.filtered(
                lambda p: 'PICK' in (p.name or '').upper()
            )

            pack_pickings = pickings.filtered(
                lambda p: 'PACK' in (p.name or '').upper()
            )

            out_pickings = pickings.filtered(
                lambda p: 'OUT' in (p.name or '').upper()
            )

            # PRIORIDAD MÁS ALTA → OUT
            if out_pickings and all(p.state == 'done' for p in out_pickings):
                order.logistic_state = 'done'
                continue

            # PACK
            if pack_pickings and all(p.state == 'done' for p in pack_pickings):
                order.logistic_state = 'shipping'
                continue

            # PICK
            if pick_pickings and all(p.state == 'done' for p in pick_pickings):
                order.logistic_state = 'packing'
                continue

            # Campo procesada
            if order.procesada:
                order.logistic_state = 'processing'
                continue

            # Confirmada pero no procesada
            order.logistic_state = 'pending'
