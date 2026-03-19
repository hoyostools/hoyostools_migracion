# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': 'Portal Sales Management',
    'odoo_version': '17.0',
    'summary': 'Portal Sales Management',
    'description': """
        Allow portal users to make sales orders from the website.
    """,
    'category': 'sales',
    'author': 'PETI Soluciones Productivas',
    'website': 'peti.com.co',
    'depends': ['website','sale'],
    'data': [
        'views/res_partner.xml',
        'templates/sale_template.xml'
    ],
    'demo': [],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        "web.assets_frontend": [
            # to add scss and js here
            "portal_sales_management/static/src/js/sale_js.js",
        ],

    },
}
