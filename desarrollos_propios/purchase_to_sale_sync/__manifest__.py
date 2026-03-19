# -*- coding: utf-8 -*-
{
    'name': 'Purchase to Sale Sync',
    'version': '17.0',
    'summary': 'Sincroniza una orden de compra como orden de venta en otra instancia Odoo',
    'category': 'Purchase',
    'author': 'Distribuciones Hoyostools',
    'depends': ['purchase', 'sale'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
