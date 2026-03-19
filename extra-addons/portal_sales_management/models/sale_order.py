from odoo import models, fields, api, tools


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_prepare_vals(self,values):
        order_line = values[1]
        date_order = fields.Datetime.from_string(values[0]['date_order']) if values[0]['date_order'] else False
        partner_id = values[0]['partner_id'] if values[0]['partner_id'] else False
        pricelist_id = values[0]['pricelist_id'] if values[0]['pricelist_id'] else False
        vals = {
            'user_id' : self.env.user.id,
            'order_line':[],
        }

        if date_order :
            vals['date_order'] = date_order
        if partner_id :
            vals['partner_id'] = int(partner_id)
        if pricelist_id :
            vals['pricelist_id'] = int(pricelist_id)
        for line in order_line:
            if line['product_id'] and line['product_uom_qty']:
                product_id = self.env['product.product'].sudo().with_company(self.env.company).browse(int(line['product_id']))
                product_uom_id = product_id.uom_id.id
                line['product_uom'] = product_uom_id
                line['tax_id'] = [(6, 0, product_id.taxes_id.ids)]
                l =(0,0,line)
                vals['order_line'].append(l)
        try:
            so = self.sudo().create(vals)
            return True
        except Exception as e:
            print(e)
            return False

