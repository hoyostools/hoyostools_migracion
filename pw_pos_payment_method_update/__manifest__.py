# -*- coding: utf-8 -*-

{
    'name': 'POS Order Payment Update',
    'category': 'Point of Sale',
    'summary': 'This apps helps you to correct/change payment method on paid pos orders | POS Order Payment Modify | Correct pos payment | POS order payment method change | Modify Pos Payment for Paid Orders',
    'description': """
This apps helps you to change payment method on paid pos orders.
""",
    'author': 'Brawil Solutions Sas',
    'version': '17.0.1.0.0',
    'depends': ['point_of_sale'],
    "data": [
        'security/ir.model.access.csv',
        'security/pos_security.xml',
        'wizard/update_payment_method_wizard.xml',
        'views/pos_order_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    "license": "LGPL-3",
}
