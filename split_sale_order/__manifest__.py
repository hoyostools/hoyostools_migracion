{
  'name' : "división de órdenes de venta",
  'version' : "17.0.0.1",
  'category' : "Sale",
  'author' : "PETI Soluciones productivas",
  'website': "http://www.peti.com.co",
  'description' : '''
          división de órdenes de venta.
  ''',
  'summary' : 'división de órdenes de venta.',
  'depends' :  ['sale', 'dev_customer_credit_limit', 'sale_exception'],
  'data' :  [
       'views/order_split.xml',
      ],
  'license': 'LGPL-3',
  'installable' : True,
  'auto_install' : False,
}
