from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _get_invoice_lines_values(self, line_values, pos_order_line):
        inv_line_vals = super(PosOrder, self)._get_invoice_lines_values(line_values, pos_order_line)
        inv_line_vals['sale_origin_id'] = line_values['record'].sale_order_origin_id.id if line_values['record'].sale_order_origin_id else False
        return inv_line_vals

