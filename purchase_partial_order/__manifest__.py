{
    'name': 'Partial Purchase Order',
    'version': '17.0.1.2.0',
    'summary': 'Allows you to split purchase orders into partial orders',
    'description': """
        This module enhances the purchase workflow by enabling partial order management:
        - ✅ Adds a checkbox on purchase order lines to select products.
        - ✅ Introduces a new field to specify the quantity to split before confirming the operation.
        - ✅ Enables the creation of a partial purchase order from an existing one.
        - ✅ Allows selecting between creating a new order or assigning to an existing one.
        - ✅ Ensures accurate stock movement and avoids duplicate deliveries.
        - ✅ Automatically resets selection fields after processing.
        - ✅ Fully integrated with stock and purchase modules.
    """,
    'category': 'Purchases',
    'author': 'Distribuciones Hoyostools',
    'website': 'https://wwww.hoyostools.com',
    'license': 'LGPL-3',
    'depends': ['purchase', 'stock'],
    'data': [
        'views/purchase_order_views.xml',
        'views/purchase_partial_order_wizard_views.xml',
        'wizards/purchase_partial_order_wizard.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
