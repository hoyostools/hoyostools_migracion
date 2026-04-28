from odoo import fields, models
from odoo.tools.float_utils import float_round


class ProductPricelistReport(models.AbstractModel):
    _inherit = 'report.product.report_pricelist'

    def _get_product_data(self, is_product_tmpl, product, pricelist, quantities):
        data = super()._get_product_data(is_product_tmpl, product, pricelist, quantities)

        image_base64 = (
            product.image_1920.decode() if isinstance(product.image_1920, bytes) else product.image_1920
        )
        data['image_1920'] = image_base64
        data['reference'] = product.default_code

        price_with_tax_dict = {}

        for qty in quantities:
            price_data = data['price'].get(qty)
            price_base = price_data['value'] if isinstance(price_data, dict) else (price_data or 0.0)
            
            # Ya no se suma impuesto, se usa el precio base directamente
            price_with_tax = price_base

            currency = pricelist.currency_id
            price_with_tax_dict[qty] = float_round(price_with_tax, precision_rounding=currency.rounding)

        data['price_with_tax'] = price_with_tax_dict
        return data