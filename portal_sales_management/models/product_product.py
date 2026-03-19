from odoo import models, fields, api, tools, _


class PurchaseOrder(models.Model):
    _inherit = "product.product"

    def find_closest_products(self,search_word):
        product_list = self.sudo().search(['|',('name','ilike',search_word),('default_code','=',search_word)],limit=10).mapped(lambda r: {'id':r.id , 'name':r.name,'internal_reference':r.default_code})
        print(product_list)
        return product_list

    def find_related_product_data(self,product_id, price_list):
        pricelist = self.env['product.pricelist'].search([('id', '=', price_list)])
        product = self.sudo().search([('id', '=', product_id)])
        price_unit = pricelist._get_product_price(
            product,
            1.0,
            uom=product.uom_id,
            date=fields.Date.today(),
        )

        return {'name': product.display_name, 'price_unit': price_unit}