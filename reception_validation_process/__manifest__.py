{
  'name' : "Verificación proceso de recepción desde compras",
  'version' : "17.0.0.1",
  'category' : "Stock",
  'author' : "PETI Soluciones productivas",
  'website': "http://www.peti.com.co",
  'description' : '''
          Adición de un campo llamado "Aprobada para Procesar" en órdenes de compra, hasta que el mismo no esté activo,
          no se permitirá realizar la validación de los albaranes.
  ''',
  'summary' : 'Verificación proceso de recepción desde compras.',
  # 'depends' :  ['purchase', 'stock', 'l10n_trading_ec'],
  'depends' :  ['purchase', 'stock'],
  'data' :  [
       'views/purchase_order_views.xml',
      ],
  'license': 'LGPL-3',
  'installable' : True,
  'auto_install' : False,
}
