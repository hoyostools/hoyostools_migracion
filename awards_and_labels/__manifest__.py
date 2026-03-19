{
    'name': 'Awards and Labels',
    'version': '17.0.1.3.0',
    'summary': 'Gestión de Premios, Tiquetes y Etiquetas para Clientes',
    'description': """
        Modulo para:
        - Configurar premios con condiciones.
        - Asignar premios a contactos.
        - Procesar acumulación.
        - Generar tiquetes imprimibles.
        - Generar sorteo.
    """,
    'category': 'Custom',
    'author': 'Distribuciones Hoyostools',
    'depends': ['base', 'contacts', 'product', 'product_brand', 'website'],
    'data': [
        # 'security/ir.model.access.xml',
        'views/award_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/sale_order_views.xml',
        'views/sorteo_views.xml',
        'views/sorteo_templates.xml',
        'data/server_actions.xml',
        'data/server_actions_sale_order.xml',
        'data/report.xml',
        'views/report_tiquetes_templates.xml',
        'views/partner_award_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
