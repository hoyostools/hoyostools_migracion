from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ht_stock_return_request_id = fields.Many2one(
        comodel_name="ht.stock.return.request",
    )
    
    invoice_ids = fields.Many2many(
        comodel_name="account.move",
        string="Notas de Crédito",
        domain="[('move_type', 'in', ['out_refund', 'in_refund'])]",
    )

    has_credit_note = fields.Boolean(
        compute="_compute_has_credit_note",
        string="¿Tiene nota de crédito?",
    )

    def _compute_has_credit_note(self):
        for picking in self:
            picking.has_credit_note = bool(picking.invoice_ids)

    def _create_backorder(self):
        """Cuando creamos un pedido pendiente de un picking en una solicitud de devolución, queremos que esté vinculado a la propia solicitud de devolución."""
        backorders = super()._create_backorder()
        rbo = backorders.filtered("backorder_id.stock_return_request_id")
        for backorder in rbo:
            backorder.stock_return_request_id = (
                backorder.backorder_id.stock_return_request_id
            )
        return backorders

    def action_create_credit_note(self):
        self.ensure_one()
        if self.state != "done":
            raise UserError("La devolución debe estar en estado 'Hecho'.")

        if self.invoice_ids:
            raise UserError("Ya existe una nota de crédito asociada a este albarán.")

        move_lines = self.move_ids.filtered(lambda m: m.state == 'done')

        invoice_lines = []
        for move in move_lines:
            sale_line = move.origin_returned_move_id.sale_line_id
            purchase_line = move.origin_returned_move_id.purchase_line_id
            price_unit = 0.0
            taxes = False

            if sale_line:
                price_unit = sale_line.price_unit
                taxes = [(6, 0, sale_line.tax_id.ids)]
            elif purchase_line:
                price_unit = purchase_line.price_unit
                taxes = [(6, 0, purchase_line.taxes_id.ids)]

            invoice_lines.append((0, 0, {
                'product_id': move.product_id.id,
                'quantity': sum(move.move_line_ids.mapped('qty_done')),
                'price_unit': price_unit,
                'tax_ids': taxes,
                'name': move.name or move.product_id.name,
            }))

        invoice_vals = {
            'move_type': 'out_refund' if self.picking_type_id.code == 'incoming' else 'in_refund',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'invoice_origin': self.origin,
        }

        invoice = self.env['account.move'].create(invoice_vals)
        invoice.message_post(body="Nota de crédito creada desde devolución: %s" % self.name)

        self.invoice_ids = [(4, invoice.id)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Nota de crédito',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
        
    def action_view_credit_notes(self):
        self.ensure_one()
        return {
            'name': 'Notas de Crédito',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.invoice_ids.ids)],
            'context': self.env.context,
        }