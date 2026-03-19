{
    'name': 'Partner Transaction Limit',
    'version': '1.0.0',
    'summary': 'Set monthly transaction limits for customers and suppliers',
    'description': """
        This module allows you to define and manage monthly transaction limits for partners (customers and suppliers). 
        Key features:
        - Set monthly sales and purchase limits for each partner.
        - Automatically calculate current-monthly sales and purchase totals.
        - Restrict new transactions when limits are exceeded.
        - Provide clear notifications and warnings to users.
    """,
    'author': 'PETI Soluciones Productivas',
    'website': 'http://www.peti.com.co',
    'category': 'Sales/CRM',
    'depends': ['sale', 'purchase', 'contacts'],
    'data': [
        'views/res_partner_views.xml',
        #'views/sale_order_views.xml',
        #'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
