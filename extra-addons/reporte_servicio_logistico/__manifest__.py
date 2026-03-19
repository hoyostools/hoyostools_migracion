{
    'name': 'Reporte Servicio Logistico',
    'version': '17.0.0.1',
    'summary': 'Generación de reportes para servicios logísticos.',
    'description': 'Módulo para generar reportes personalizados de servicios logísticos en Odoo.',
    'category': 'Reporting',
    'author': 'PETI Soluciones Productivas',
    'website': 'https://www.peti.com.co',
    'license': 'LGPL-3',
    'depends': ['sale_management', 'sale', 'base'],
    'data': [
        'views/report_servicio_logistico.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
