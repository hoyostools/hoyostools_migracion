# -*- coding: utf-8 -*-


{
    "name": "Point of sale cashback",
    "version": "17.0.0.1",
    "category": "Punto de venta",
    'summary': 'POS nuevo metodo',
    "description": """

    El módulo de devolución de dinero agrega una opción para usar un nuevo método de pago en el punto de venta

    """,
    "author": "PETI Soluciones productivas",
    "website": "https://www.peti.com.co",
    "depends": ['base', 'point_of_sale','loyalty','sale'],
    "data": [
        'views/account_journal.xml',
    ],
    'assets': {
        'point_of_sale.assets_prod': [
            'cashback/static/src/js/PaymentScreen.js',
            #'cashback/static/src/js/PartnerListScreen.js',
            'cashback/static/src/xml/pos.xml',
        ],
    },
    'license': 'OPL-1',
    "auto_install": False,
    "installable": True,    
}
