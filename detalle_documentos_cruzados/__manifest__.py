# -*- coding: utf-8 -*-
{
    'name': "Detalle documentos cruzados",

    'summary': """
        Personaliza el recibo de pago indicando de manera más especifica la información de las facturas asociadas""",

    'description': """
        Detalle documentos cruzados
    """,

    'author': "PETI Soluciones Productivas",
    'website': "http://www.peti.com.co",

    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['account'],

    'data': [
        'report/report_payment_receipt_document_inherit.xml',
    ],
    'license': 'LGPL-3',

}
