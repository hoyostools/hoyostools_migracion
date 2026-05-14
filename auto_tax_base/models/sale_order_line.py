from odoo import api, models, fields
from collections import defaultdict

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def write(self,vals):
        res = super().write(vals)
        if 'tax_id' not in vals:
            self._compute_tax_id()
        return res

    def create(self,vals):
        res = super().create(vals)
        if 'tax_id' not in vals:
            res._compute_tax_id()
        return res

    @api.depends('product_id', 'company_id')
    @api.constrains('price_subtotal','product_uom_qty')
    def _compute_tax_id(self):
        super()._compute_tax_id()
        for line in self:
            order = line.order_id
            fiscal_position = order.fiscal_position_id
            valid_taxes = self.env['account.tax']
            if fiscal_position:
                valid_taxes = fiscal_position.map_tax(valid_taxes)
            delete_taxes = line.order_id.order_line.tax_id.filtered(
                lambda t: t.base_amount > line.order_id.amount_untaxed and t.base_check == True)
            reteiva_taxes = line.order_id.order_line.tax_id.filtered(
                lambda t: t.reteiva == True)
            if delete_taxes:
                line.order_id.order_line.tax_id -= delete_taxes
            if valid_taxes:
                line.order_id.order_line.tax_id += valid_taxes
            if reteiva_taxes and fiscal_position.aplica_reteiva:
                line.order_id.order_line.tax_id += reteiva_taxes.impuesto_reteiva

    def _get_protected_fields(self):
        lista = super()._get_protected_fields()
        lista.remove('tax_id')
        return lista
