# -*- coding: utf-8 -*-
{
    'name': 'Descuento en lineas de producto',
    'summary': 'Descuento en lineas de producto de las ordenes de venta',
    'description': 'Descuento personalizado en lineas de producto de las ordenes de venta para hoyos tools',
    'author': 'Distribuciones HOYOSTOOLS',
    'website': 'https://www.hoyostools.com.co',
    'category': 'Tools',
    'version': '17.0.1.0.0',
    'license': 'OPL-1',
    'depends': [
        'sale',
        'product',
        'account',
        'base',
    ],
    'data': [
        'views/website_sale_inherit.xml',
        'views/product_template_views.xml',
    ],
}
