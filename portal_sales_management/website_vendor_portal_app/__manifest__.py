# -*- coding: utf-8 -*-
{
    "name" : "Online Vendor Portal- Website Supplier Portal",
    "author": "Edge Technologies",
    "version" : "17.0.1.0",
    "live_test_url":'https://youtu.be/pZiOyalg3lw',
    "images":["static/description/main_screenshot.png"],
    'summary': 'Purchase portal price change website vendor portal price change for purchase order rfq portal vendor price portal change shipment date from portal supplier purchase portal purchase vendor portal for purchase price change cost price from vendor web portal.',
    "description": """
        This app helps user to add the vendor price in the order in the website.
    """,
    "license" : "OPL-1",
    "depends" : ['base','website','website_sale','purchase'],
    "data": [
        'views/purchase_order.xml',
        'views/purchase_template.xml',
        'report/report_purchase_order.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_vendor_portal_app/static/src/js/vendor_price.js',
        ],
    },
    "auto_install": False,
    "installable": True,
    "price": 35,
    "currency": 'EUR',
    "category" : "eCommerce",

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
