{
    'name': 'Purchase Logbook',
    'version': '17.0.5.0',
    'summary': 'Bitácora para el módulo de Compras',
    'category': 'Purchase',
    'author': 'Brawil Solutions SAS',
    
    'depends': ['purchase'],
    'data': [
        'views/purchase_logbook_views.xml',
        'views/menuitems.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
