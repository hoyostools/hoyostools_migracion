# -*- coding: utf-8 -*-
{
    'name': 'Point of Sale Stock Transfer',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "Allows to Directly Transfer the Stock From the Current POS"
               " Session",
    'description': "This module allows for the immediate movement of stock "
                   "within the same point-of-sale (POS) session.",
    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",
    'depends': ['base', 'point_of_sale', 'stock'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/stock_picking_type_views.xml',
        'views/stock_location_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            '/stock_transfer_in_pos/static/src/xml/stock_transfer_button.xml',
            '/stock_transfer_in_pos/static/src/xml/transfer_ref_popup.xml',
            '/stock_transfer_in_pos/static/src/xml/transfer_create_popup.xml',
            '/stock_transfer_in_pos/static/src/js/stock_transfer.js',
            '/stock_transfer_in_pos/static/src/js/transfer_create_popup.js',
            '/stock_transfer_in_pos/static/src/js/transfer_ref_popup.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
