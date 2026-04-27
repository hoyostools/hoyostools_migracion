# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
##########################################################################
{
    'name': 'Product Catalogs',
    "summary": "Odoo Product Catalogs allows you to print different types of catalogs for the products in Odoo. Moreover, the module allows you to set the product details which need to be added to the catalog.",
    'category': "Sales",
    'version': '1.0.0',
    'sequence': 1,
    "license":  "Other proprietary",
    'author': 'Webkul Software Pvt. Ltd.',
    "website":  "https://store.webkul.com",
    "description":  """
                    Odoo Product Catalogs
                    Product catalogs in Odoo
                    Odoo Catalogs
                    Catalogs
                    Product Catalogs
		             """,
    'depends': ['website_sale'],
    'data': [
            'security/ir.model.access.csv',
            'wizard/product_catalogs_view.xml',
            'reports/product_catalog_report.xml',
            'views/catalog_frontpage_view.xml',
    ],
    "images" :  ['static/description/Banner.gif'],
    "application":  True,
    'installable': True,
    "auto_install":  False,
    'active': False,
    'price': 45,
    "currency": "USD",
    # "pre_init_hook" : "pre_init_check",
}
