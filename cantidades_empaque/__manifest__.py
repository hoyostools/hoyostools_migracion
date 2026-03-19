{
    "name": "Cantidades en empaque",
    "version": "17.0.1.1.0",
    "category": "packing",
    "summary": "Indicar cantidades a empacar",
    'depends': ['stock', 'stock_delivery', 'stock_barcode', 'campos_hoyos'],
    "data": [
        "views/choose_delivery_package.xml",
        'views/stock_picking.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'cantidades_empaque/static/src/xml/barcode_extension.xml',
        ],
    },
    "installable": True,
    "application": False,
}
