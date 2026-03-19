{
    'name': 'Wave Recolección Status',
    'version': '17.0.1.0.0',
    'author': 'Brawil Solutions',
    'website': 'https://brawilsolutions.odoo.com',
    'license': 'LGPL-3',
    'depends': ['stock'],
    'category': 'Warehouse',
    'summary': 'Agrega un campo booleano para indicar si ya comenzó la recolección en una ola',
    'data': [
        'views/stock_picking_wave_views.xml',
    ],
    'installable': True,
    'application': False,
}
