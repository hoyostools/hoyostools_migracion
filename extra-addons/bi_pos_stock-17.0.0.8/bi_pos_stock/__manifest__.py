# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


{
    "name": "POS Stock in Odoo",
    "version": "17.0.0.8",
    "category": "Point of Sale",
    "depends": ['base', 'sale_management', 'stock', 'point_of_sale'],
    "author": "BROWSEINFO",
    'summary': 'Display POS Stock Quantity on POS screen stock Product stock in POS product stock Quantity POS Order stock POS Mobile POS Inventory management pos stocks pos item stock point of sale stock POS Product Warehouse Quantity pos product qty pos product Quantity',
    'price': 29,
    'currency': "EUR",
    "description": """
    odoo pos stock point of sales stocks pos stocks
    odoo pos inventory POS Stock - Available Qty
    odoo stock in pos odoo pos current stock of products

    odoo point of sales stock point of sale stocks point of sales stocks odoo
    odoo point of sales inventory point of sales Stock - Available Qty odoo
    odoo stock in point of sales odoo point of sales current stock of products odoo


    odoo point of sale stock point of sales stocks point of sale stocks odoo
    odoo point of sale inventory point of sale Stock - Available Qty odoo
    odoo stock in point of sale odoo point of sale current stock of products odoo

    pos 
    Purpose :- 
    odoo Display Stock in POS Display Stock Quantity on POS
    odoo POS warning stock Warning on POS 
    odoo POS stock management odoo Stock management on POS Product stock on POS
    odoo POS product stock POS product stock on hand Display product stock on POS
    odoo Point of sale stock odoo Display Stock in Point of Sales 
    odoo Display Stock Quantity on Point of Sales odoo Point of Sales warning stock  Warning on Point of Sales
    odoo Point of Sales stock management odoo Stock management on Point of Sales
    odoo Product stock on Point of Sales odoo Point of sales product stock 
    odoo Point of sales product stock on hand Display product stock on Point of Sales,

    odoo Point of sales stock odoo Display Stock in Point of Sales 
    odoo Display Stock Quantity on Point of Sale odoo Point of Sales warning stock  Warning on Point of Sales odoo
    odoo Point of Sale stock management odoo Stock management on Point of Sales odoo
    odoo Product stock on Point of Sale odoo Point of sales product stock odoo
    odoo Point of sale product stock on hand Display product stock on Point of Sale odoo
    """,
    "website": "https://www.browseinfo.com/demo-request?app=bi_pos_stock&version=17&edition=Community",
    "data": [
        'views/custom_pos_config_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'bi_pos_stock/static/src/css/stock.css',

            'bi_pos_stock/static/src/app/generic_components/product_card/product_card.xml',
            'bi_pos_stock/static/src/app/generic_components/product_card/product_card.js',

            'bi_pos_stock/static/src/app/screens/product_screen/product_list/product_list.js',

            'bi_pos_stock/static/src/app/screens/product_screen/product_low_stock_screen/product_low_stock_screen.js',
            'bi_pos_stock/static/src/app/screens/product_screen/product_low_stock_screen/product_low_stock_screen.xml',

            'bi_pos_stock/static/src/app/screens/product_screen/product_low_stock_screen/low_stock_line/low_stock_line.js',
            'bi_pos_stock/static/src/app/screens/product_screen/product_low_stock_screen/low_stock_line/low_stock_line.xml',

            'bi_pos_stock/static/src/app/generic_components/order_widget/order_widget.js',
            'bi_pos_stock/static/src/app/generic_components/order_widget/order_widget.xml',

            'bi_pos_stock/static/src/app/navbar/navbar.js',
            'bi_pos_stock/static/src/app/navbar/navbar.xml',
            
            'bi_pos_stock/static/src/app/store/models.js',
        ],
    },
    "auto_install": False,
    "installable": True,
    "live_test_url": 'https://www.browseinfo.com/demo-request?app=bi_pos_stock&version=17&edition=Community',
    "images": ['static/description/Banner.gif'],
    'license': 'OPL-1',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
