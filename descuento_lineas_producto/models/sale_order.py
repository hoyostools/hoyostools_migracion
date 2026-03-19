from odoo import fields, models, api
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def verify_group_discount(self):
        for group in self.env.user.groups_id:
            if group.display_name in ['Ventas / Administrador', 'Ventas / Asistentes Comerciales',
                                      'Ventas / Dir Comerciales', 'Compra / Analista de Compras',
                                      'Compra / Administrador', 'Compra / Usuario']:
                return True
        return False

    def calculate_discount_general(self):
        self.ensure_one()
        discount_permission_group = self.verify_group_discount()
        if self.product_template_id and self.product_template_id.applicable_sale_order and not discount_permission_group and not self.order_id.skip_calculate_discount:
            valor_a = self.product_template_id.valor_a
            valor_b = self.product_template_id.valor_b
            if valor_a >= self.product_uom_qty >= valor_b:
                if not self.discount <= self.product_template_id.descuento_rango:
                    self.discount = self.product_template_id.descuento_rango
            if self.product_uom_qty > valor_a:
                if not self.discount <= self.product_template_id.descuento_mayor:
                    self.discount = self.product_template_id.descuento_mayor
            if self.product_uom_qty < valor_b:
                self.discount = self.discount

    @api.onchange('product_uom_qty')
    def calculate_discount(self):
        self.ensure_one()
        if self.product_template_id and self.product_template_id.applicable_sale_order and not self.order_id.skip_calculate_discount:
            valor_a = self.product_template_id.valor_a
            valor_b = self.product_template_id.valor_b
            if valor_a >= self.product_uom_qty >= valor_b:
                self.discount = self.product_template_id.descuento_rango
            if self.product_uom_qty > valor_a:
                self.discount = self.product_template_id.descuento_mayor
            if self.product_uom_qty < valor_b:
                self.discount = 0

    def calculate_discount_write(self, cantidad, discount, is_change):
        self.ensure_one()
        if self.product_template_id and not self.order_id.skip_calculate_discount:
            valor_a = self.product_template_id.valor_a
            valor_b = self.product_template_id.valor_b
            if valor_a >= cantidad >= valor_b and not self.discount <= self.product_template_id.descuento_rango:
                return self.product_template_id.descuento_rango
            elif cantidad > valor_a and not self.discount <= self.product_template_id.descuento_mayor:
                return self.product_template_id.descuento_mayor
            elif cantidad < valor_b:
                return 0
            else:
                return discount if is_change else self.discount

    @api.model
    def create(self, values):
        res = super(SaleOrderLine, self).create(values)
        order = self.env['sale.order'].browse(values.get('order_id'))

        if not order.website_id:
            for record in res:
                record.calculate_discount_general()
        return res

    def write(self, values):
        if not self.order_id.website_id:
            if 'product_uom_qty' in values and values['product_uom_qty']:
                if 'discount' in values:
                    values['discount'] = self.calculate_discount_write(values['product_uom_qty'], values['discount'], 1)
                else:
                    values['discount'] = self.calculate_discount_write(values['product_uom_qty'], 0, 0)
        res = super(SaleOrderLine, self).write(values)
        return res

    @api.onchange('discount')
    def maximum_discount(self):
        self.ensure_one()
        discount_permission_group = self.verify_group_discount()
        if not discount_permission_group:
            valor_a = self.product_template_id.valor_a
            valor_b = self.product_template_id.valor_b
            if valor_a >= self.product_uom_qty >= valor_b:
                if self.discount > self.product_template_id.descuento_rango:
                    valor = self.product_template_id.descuento_rango
                    raise ValidationError('El valor de descuento máximo editable es ' + str(valor))
            if self.product_uom_qty > valor_a:
                if self.discount > self.product_template_id.descuento_mayor:
                    valor = self.product_template_id.descuento_mayor
                    raise ValidationError('El valor de descuento máximo editable es ' + str(valor))
            if self.product_uom_qty < valor_b:
                self.discount = 0


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    skip_calculate_discount = fields.Boolean(default=False)

    def action_unlock(self):
        ''' En caso de que se desbloquee, estando confirmada, no debe recalcular los descuentos '''
        for ov in self:
            if ov.state == 'sale':
                ov.skip_calculate_discount = True
        return super().action_unlock()

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id_show_update_prices(self):
        self.ensure_one()
        self.show_update_pricelist = False
        if self.pricelist_id:
            self._origin.pricelist_id = self.pricelist_id
            self._origin._recompute_prices()
            self._recompute_prices()

    @api.onchange('order_line')
    def compute_order_line_discount(self):
        for record in self:
            for rec in record.order_line:
                rec.calculate_discount_general()

    def _cart_update_order_line(self, product_id, quantity, order_line, **kwargs):
        order_lines = super()._cart_update_order_line(product_id, quantity, order_line, **kwargs)
        for line in order_lines:
            product = line.product_id
            qty = line.product_uom_qty
            if product.valor_b <= qty <= product.valor_a:
                line.discount = product.descuento_rango
            elif qty > product.valor_a and product.descuento_mayor:
                line.discount = product.descuento_mayor
            else:
                line.discount = 0

        return order_lines
