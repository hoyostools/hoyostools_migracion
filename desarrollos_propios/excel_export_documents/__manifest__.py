{
    'name': 'Exportar Documentos a Excel',
    'version': '17.0.1.3.0',
    'depends': ['sale', 'account'],
    'author': 'Distribuciones Hoyostools',
    'category': 'Tools',
    'description': 'Agrega botones para exportar órdenes de venta y asientos contables a Excel',
    'installable': True,
    'application': False,
    'data': [
        'views/sale_order_view.xml',
        'views/account_move_view.xml',
    ],
}
