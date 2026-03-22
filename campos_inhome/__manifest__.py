# -*- coding: utf-8 -*-
{
    'name': "Campos inhome",

    'summary': """
        Campos inhome
        """,

    'description': """
        Campos inhome
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '18.0.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['stock'],

    'data': [
        'views/stock_quant_view.xml',
    ],
    'license': 'LGPL-3',
}
