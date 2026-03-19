from odoo import models, _, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('move_type', 'move_ids.state', 'move_ids.picking_id')
    def _compute_state(self):
        for picking in self:
            moves_to_backorder = picking._get_moves_to_backorder()
            if moves_to_backorder and 'PACK' in picking.name and len(self.sale_id.picking_ids.filtered(lambda s: s.state != 'done' and 'PICK' in s.name)) <= 1 and len(self.sale_id.picking_ids.filtered(lambda s: 'PICK' in s.name)) > 1:
                picking.state = 'assigned'
            else:
                super()._compute_state()

    def _create_backorder(self):
        """ This method is called when the user chose to create a backorder. It will create a new
        picking, the backorder, and move the stock.moves that are not `done` or `cancel` into it.
        """
        backorders = self.env['stock.picking']
        bo_to_assign = self.env['stock.picking']
        for picking in self:
            moves_to_backorder = picking._get_moves_to_backorder()
            moves_to_backorder._recompute_state()
            if moves_to_backorder:
                backorder_picking = picking._create_backorder_picking()
                moves_to_backorder.write({'picking_id': backorder_picking.id, 'picked': False})
                moves_to_backorder.move_line_ids.package_level_id.write({'picking_id': backorder_picking.id})
                moves_to_backorder.mapped('move_line_ids').write({'picking_id': backorder_picking.id})
                backorders |= backorder_picking
                picking.message_post(
                    body=_('The backorder %s has been created.', backorder_picking._get_html_link())
                )
                if backorder_picking.picking_type_id.reservation_method == 'at_confirm':
                    bo_to_assign |= backorder_picking
        if bo_to_assign:
            bo_to_assign.action_assign()
        for pick in backorders:
            if 'PICK' in pick.name:
                destino = self.env['stock.location'].search([('audit_pick_location','=',True)],limit=1)
                if destino:
                    pick.location_dest_id = destino
            if 'PACK' in pick.name:
                destino = self.env['stock.location'].search([('audit_pack_location','=',True)],limit=1)
                if destino:
                    pick.location_dest_id = destino
        return backorders
