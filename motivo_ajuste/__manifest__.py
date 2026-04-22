{
    'name': 'Motivos de Ajuste de Inventario',
    'version': '1.0',
    'author': 'Distribuciones Hoyostools',
    'category': 'Inventory',
    'summary': 'Agregar motivos de ajuste al inventario',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/motivo_ajuste_views.xml',
        'views/stock_inventory_inherit_view.xml',
    ],
    'installable': True,
    'application': False,
}
