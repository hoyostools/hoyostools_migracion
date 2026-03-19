# -*- coding: utf-8 -*-
{
    'name': 'Tablero de Oleadas',
    'summary': 'Tablero Gestión de Órdenes de Venta y Asignación de Wave Para Picking y Responsable de Empaque',
    'description': 'Tablero Gestión de Órdenes de Venta y Asignación de Wave Para Picking y Responsable de Empaque',
    'author': 'PETI Soluciones Productivas',
    'website': 'https://www.peti.com.co',
    'category': 'Tools',
    'version': '17.0.1.0.0',
    'license': 'OPL-1',
    'depends': [
        'sale',
        'product',
        'account',
        'base',
        'stock'
    ],

    'data': [
        'data/ir_cron.xml',
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'sale_order_waves/static/src/xml/button_tree.xml',
            'sale_order_waves/static/src/xml/tablero_productividad.xml',
            'sale_order_waves/static/src/js/button_tree.js',
            'sale_order_waves/static/src/js/tablero_productividad.js',
            'sale_order_waves/static/lib/js/index.js',
            'sale_order_waves/static/lib/js/xy.js',
            'sale_order_waves/static/lib/js/radar.js',
            'sale_order_waves/static/lib/js/Animated.js',
        ],
    },
}
