# -*- coding: utf-8 -*-
{
    'name': "Producto con orden de compra",

    'summary': """
        Campo numero de Orden de Compra y Fecha de Recepcion
        """,

    'description': """
        "En la Plantilla del Producto se han agregado el campo de Numero de Orden
        de Compra como la fecha de recepcion del producto
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Products',
    'version': '17.1',

    # any module necessary for this one to work correctly
    'depends': ['product','purchase'],

    # always loaded
    'data': [
        'views/product_template.xml',
    ],
    'license': 'LGPL-3',
}
