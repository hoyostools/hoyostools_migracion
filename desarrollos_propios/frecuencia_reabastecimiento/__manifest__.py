{
    'name': 'Frecuencia de Reabastecimiento',
    'version': '17.0.1.5.0',
    'category': 'Inventory',
    'author': 'Distribuciones Hoyostools',
    'summary': 'Campos de frecuencia de reabastecimiento sincronizados con reglas',
    'depends': ['stock', 'product', 'campos_hoyos', 'purchase'],
    'data': [
        'views/product_template_views.xml',
        'views/stock_quants_views.xml',
        'views/stock_location_views.xml',
        'views/stock_warehouse_orderpoint_views.xml',
        ],
    'installable': True,
    'application': False,
}