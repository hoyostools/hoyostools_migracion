# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Remove POS Order Lines',
    'summary': """Remove POS Order Lines""",
    'sequence': 901,
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'author': 'Software Box',
    'website': 'http://softwarebox18@gmail.com',
    'module_type': 'industries',
    'depends': ['point_of_sale'],
    'data': [
        # 'views/views.xml',
        # 'security/ir.model.access.csv',
    ],
    'images': ['static/description/main.PNG'],
    'installable': True,
    'application': True,
    'assets': {
        'point_of_sale._assets_pos': [
            # js
            'mh_remove_pos_orderline/static/src/js/clear_all_orderlines.js',
            # theme
            'mh_remove_pos_orderline/static/src/app/screens/product_screen/custom_product_screen.xml',
            'mh_remove_pos_orderline/static/src/app/screens/product_screen/orderline.xml',
            'mh_remove_pos_orderline/static/src/scss/custom.scss',
        ]
    },
    'license': 'OPL-1',
}
