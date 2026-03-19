# Copyright 2026 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

{
    'name': 'Multiple Packages',
    'version': '17.0.1.0.0',
    'author': 'VentorTech',
    'website': 'https://ventor.tech/',
    'license': 'LGPL-3',
    'installable': True,
    'images': ['static/description/icon.png'],
    'summary': 'Pack one move line into multiple packages',
    'depends': [
        'ventor_base',
        'delivery',
        'stock_delivery',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/stock_move_line.xml',
        'wizard/multiple_pack_wizard_view.xml',
        'wizard/package_details_wizard_view.xml',
    ],
}
