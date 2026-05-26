{
    'name': 'Traslados Masivos',
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Traslado masivo desde stock.quants',
    'author': 'Distribuciones Hoyostools',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/stock_quant_mass_transfer_views.xml',
        'views/stock_quant_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}