{
    'name': 'Stock Quant Inventory Tracker',
    'version': '17.0.1.0.0',
    'summary': 'Agrega campo contado_por al modificar inventory_quantity',
    'description': 'Este módulo extiende la funcionalidad de stock.quant para rastrear el usuario que realiza el conteo de inventario mediante el campo contado por.',
    'author': 'Distribuciones Hoyostools',
    'depends': ['stock'],
    'data': [
        'views/stock_quant_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
