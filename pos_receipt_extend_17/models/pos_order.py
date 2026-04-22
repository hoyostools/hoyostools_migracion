from odoo import models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'

    cufe = fields.Char(string="CUFE/CUDE", store=True)
    img_cufe = fields.Char(string="CUFE/CUDE QR", store=True)

    def _generate_pos_order_invoice(self):
        res = super()._generate_pos_order_invoice()

        for order in self:
            move = order.account_move

            if move and move.dian_document_lines:
                order.cufe = move.dian_document_lines[0].cufe_cude
                order.img_cufe = move.dian_document_lines[0].qr_code_dian_img

        return res