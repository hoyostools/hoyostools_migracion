{
    "name": "Auto Inventory Location",
    "version": "17.0.1.2",
    "author": 'Distribuciones Hoyostools Sas',
    "depends": [
        "stock",
        "purchase",
        "frecuencia_reabastecimiento"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/auto_location_views.xml",
        "views/auto_location_responsible_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
}