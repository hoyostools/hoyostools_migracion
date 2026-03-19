{
    'name': "Captura y actualización de criterios de productos en recepción",
    'version': "17.0.0.1",
    'category': "Stock",
    'author': "PETI Soluciones productivas",
    'website': "http://www.peti.com.co",
    'description': '''en el modulo de inventarios, en el tipo de Operación de recibo o recepción de los almacenes que 
  tengan activa la opción comprar para reabastecer, el desarrollo despliega una pantalla desde la operación de 
  recepción que permite capturar y actualizar los criterios del maestro de productos y reglas de reordenamiento.
  ''',
    'depends': ['stock', 'product', 'product_manufacturer', 'sale'],
    'data': ['security/ir.model.access.csv',
             'views/stock_picking.xml',
             'views/product_views.xml',
             'views/user_criteria_update_views.xml',
             'views/stock_picking_type_views.xml',
             'views/stock_warehouse_orderpoint_views.xml'],

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,

    'assets': {
        'web.assets_backend': [
            'product_criteria_update/static/src/js/barcode_call.xml',
            'product_criteria_update/static/src/js/barcode_call.js',
        ],
    },
}
