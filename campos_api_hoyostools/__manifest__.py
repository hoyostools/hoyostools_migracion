{
    "name": "Campos API para Productos",
    "version": "17.0.2.0",
    "summary": "Campos creados para la integración vía API con Distribuciones Hoyostools.",
    "description": """
Modulo que añade campos personalizados a los productos para facilitar la integración vía API con Distribuciones Hoyostools.
""",
    "author": "Distribuciones Hoyostools",
    "website": "https://wwww.hoyostools.com",
    "category": "Inventory",
    "license": "LGPL-3",
    "depends": [
        "product", "purchase", "sale",
    ],
    "data": [
        'views/product_template_views.xml',
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}

