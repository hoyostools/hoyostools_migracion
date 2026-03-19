from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _search_get_detail(self, website, order, options):
        res = super(ProductTemplate, self)._search_get_detail(website, order, options)

        # Añadir a search_fields barcode
        if 'product_variant_ids.barcode' not in res['search_fields']:
            res['search_fields'].append('product_variant_ids.barcode')

        # Añadir a mapping
        if 'product_variant_ids.barcode' not in res['mapping']:
            res['mapping']['product_variant_ids.barcode'] = {
                'name': 'barcode',
                'type': 'text',
                'match': True
            }

        return res
