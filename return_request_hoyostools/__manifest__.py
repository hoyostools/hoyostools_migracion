{
    'name': 'update_return_request',
    'summary': 'Agrega unas mejoras especificas en el modulo de devoluciones para la empresa de hoyostools',
    'description': 'Agrega atributos a vistas, crea condiciones para algunos objetos y crea campos nuevos para el modulo'
                   ' de solicitudes de devoluciones',
    'author': 'PETI Soluciones Productivas',
    'website': 'https://www.peti.com.co',
    'category': 'Uncategorized',
    'version': '17.0.1.0.0',
    'license': 'OPL-1',
    'depends': [
        'sale',
        'stock',
        'stock_return_request'
    ],

    'data': [
        'views/stock_request_hoyostools.xml',
    ],

}