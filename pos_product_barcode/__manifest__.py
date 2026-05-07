# -*- coding: utf-8 -*-
{
    'name': "POS Product Barcode",
    'summary': """
        Product barcode in POS product window """,
    'description': """
        Product barcode in POS product window. 
    """,
    'author': "Loyal IT Solutions Pvt Ltd",
    'website': "https://www.loyalitsolutions.com",
    'maintainer': "Loyal IT Solutions",
    'category': 'Point of Sale',
    'version': '17.0.1.0.0',
    'depends': ['base', 'point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_product_barcode/static/src/xml/barcode.xml',
        ],

    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

    'images': ['static/description/banner.png'],
}

