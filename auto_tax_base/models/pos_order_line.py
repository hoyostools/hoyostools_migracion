from odoo import api, models, fields

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.constrains('lines')
    def update_values_pos(self):
        for line in self.lines:
            line._get_tax_ids_after_fiscal_position()

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    def write(self,vals):
        res = super().write(vals)
        if 'tax_ids_after_fiscal_position' not in vals:
            self._get_tax_ids_after_fiscal_position()
        return res

    def create(self,vals):
        res = super().create(vals)
        res._get_tax_ids_after_fiscal_position()
        return res

    @api.constrains('order_id','order_id.fiscal_position_id')
    @api.depends('order_id', 'order_id.fiscal_position_id')
    def _get_tax_ids_after_fiscal_position(self):
        super()._get_tax_ids_after_fiscal_position()
        for line in self:
            delete_taxes = line.order_id.lines.tax_ids_after_fiscal_position.filtered(
                lambda t: t.base_amount > (line.order_id.amount_total - line.order_id.amount_tax) and t.base_check == True)
            reteiva_taxes = line.order_id.lines.tax_ids_after_fiscal_position.filtered(
                lambda t: t.reteiva == True)
            if delete_taxes:
                line.order_id.lines.tax_ids_after_fiscal_position -= delete_taxes
            if reteiva_taxes and line.order_id.fiscal_position_id.aplica_reteiva:
                line.order_id.lines.tax_ids_after_fiscal_position += reteiva_taxes.impuesto_reteiva
