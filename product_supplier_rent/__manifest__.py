{
    'name': 'Product Supplier Rent',
    'version': '17.0.1.11.0',
    'summary': 'Add additional fields to product.supplierinfo and display the First Supplier Suggested Price in product.template',
    'description': """
        This module extends the functionality of Odoo to:
        - Add fields in `product.supplierinfo` (Factory Price, Factory Currency, Yuan Exchange Rate, Settlement Factor, Estimated Cost).
        - Automatically calculate the `Estimated Cost` based on the supplier's currency.
        - Show the `Suggested Price` of the first supplier in `product.template`.
        - Place the `Suggested Price` field in the General Information tab of the product.
    """,
    'category': 'Inventory',
    'author': 'Distribuciones Hoyostools sas',
    'website': 'https://www.hoyostools.com',
    'license': 'LGPL-3',
    'depends': ['product', 'account', 'base', 'purchase', 'sale', 'campos_hoyos'],
    'data': [
        'views/product_supplierinfo_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
}