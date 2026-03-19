from odoo import models, fields, api
from odoo.exceptions import UserError

class StockTransferWizard(models.TransientModel):
    _name = 'stock.transfer.wizard'
    _description = 'Wizard de traslado'

    line_ids = fields.One2many('stock.transfer.wizard.line', 'wizard_id')

    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Tipo de operación',
        required=True,
        domain="[('code','=','internal')]"
    )

    state_option = fields.Selection([
        ('draft', 'Listo'),
        ('done', 'Hecho')
    ], string="Estado", required=True)

    user_id = fields.Many2one('res.users', string="Responsable")

    def action_create_transfer(self):

        if not self.line_ids:
            raise UserError("No hay líneas para trasladar")

        for line in self.line_ids:
            if line.qty_to_move > line.available_qty:
                raise UserError("No puedes trasladar más de lo disponible")

        picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.line_ids[0].location_id.id,
            'location_dest_id': self.line_ids[0].location_dest_id.id,
            'user_id': self.user_id.id if self.user_id else False,
        })

        moves = []

        for line in self.line_ids:
            moves.append((0, 0, {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty_to_move,
                'product_uom': line.product_id.uom_id.id,
                'location_id': line.location_id.id,
                'location_dest_id': line.location_dest_id.id,
            }))

        picking.move_ids_without_package = moves

        picking.action_confirm()

        picking.action_assign()

        if self.state_option == 'done':
            for move in picking.move_ids:
                move.quantity_done = move.product_uom_qty

            picking.button_validate()

        return {'type': 'ir.actions.act_window_close'}
