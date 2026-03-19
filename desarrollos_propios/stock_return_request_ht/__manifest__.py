{
    "name": "Stock Return Request HT",
    "version": "17.0.1.7.0",
    "category": "Stock",
    "website": "https://www.hoyostools.com",
    "author": "Distribuciones Hoyostools",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ht_stock_return_request_data.xml",
        "views/ht_stock_return_request_views.xml",
        "report/stock_return_report.xml",
        "wizard/ht_suggest_return_request.xml",
    ],
}
