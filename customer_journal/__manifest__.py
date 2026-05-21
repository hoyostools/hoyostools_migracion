{
    'name': 'Diarios Habilitados',
    'version': '17.0.0.0.0',
    'summary': 'Agrega campo diarios habilitados para restringir Diarios al usuario',
    'author': 'Distribuciones Hoyostools',
    'depends': ['account','base'],
    'data': [
        'views/res_users.xml',
        'data/ir_rule.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
