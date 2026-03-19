{
    'name': 'Kardex Integration',
    'version': '17.0.1.1.0',
    'summary': 'Integración con Kardex Power Pick Global',
    'category': 'Inventory',
    'author': 'Distribuciones Hoyostools SAS',
    'license': 'LGPL-3',
    'depends': ['stock'],
    'data': [
        'views/stock_picking_view.xml',
        'views/res_config_settings_view.xml',
        'data/kardex_cron.xml',
    ],
    'installable': True,
    'application': False,
}
