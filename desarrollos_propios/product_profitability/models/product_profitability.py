# from odoo import models, fields, api

# class ProductTemplate(models.Model):
#     _inherit = 'product.template'

#     profitability = fields.Float(
#         string='Rentabilidad',
#         compute='_compute_profitability',
#         store=True,
#         help='Calcula la rentabilidad como ((list_price - standard_price) / list_price) * 100'
#     )

#     @api.depends('list_price', 'standard_price')
#     def _compute_profitability(self):
#         for product in self:
#             if product.list_price > 0:
#                 product.profitability = ((product.list_price - product.standard_price) / product.list_price) * 100
#             else:
#                 product.profitability = 0.0


from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    profitability = fields.Float(
        string='Rentabilidad',
        compute='_compute_profitability',
        store=True,
        help='Calcula la rentabilidad como ((list_price - standard_price) / list_price) * 100'
    )

    price_10 = fields.Float(
        string='Precio con 10%',
        compute='_compute_prices',
        store=True,
        help='Calcula el precio con el 10% de descuento y el IVA correspondiente'
    )

    price_15 = fields.Float(
        string='Precio con 15%',
        compute='_compute_prices',
        store=True,
        help='Calcula el precio con el 15% de descuento y el IVA correspondiente'
    )

    price_20 = fields.Float(
        string='Precio con 20%',
        compute='_compute_prices',
        store=True,
        help='Calcula el precio con el 15% de descuento y el IVA correspondiente'
    )
    
    price_30 = fields.Float(
        string='Precio con 30%',
        compute='_compute_prices',
        store=True,
        help='Calcula el precio con el 15% de descuento y el IVA correspondiente'
    )
    
    price_40 = fields.Float(
        string='Precio con 40%',
        compute='_compute_prices',
        store=True,
        help='Calcula el precio con el 15% de descuento y el IVA correspondiente'
    )
    
    price_50 = fields.Float(
        string='Precio con 50%',
        compute='_compute_prices',
        store=True,
        help='Calcula el precio con el 15% de descuento y el IVA correspondiente'
    )
    
    @api.depends('list_price', 'standard_price', 'taxes_id')
    def _compute_profitability(self):
        for product in self:
            list_price_no_tax = product.list_price
            if product.taxes_id:
                tax = product.taxes_id[0]
                if tax.price_include:
                    # Si el precio incluye impuesto, se debe quitar para obtener el neto
                    list_price_no_tax = product.list_price / (1 + (tax.amount / 100))
                else:
                    # Si el impuesto no está incluido, el precio ya es neto
                    list_price_no_tax = product.list_price
            else:
                list_price_no_tax = product.list_price  # Sin impuestos

            if list_price_no_tax > 0:
                product.profitability = ((list_price_no_tax - product.standard_price) / list_price_no_tax) * 100
            else:
                product.profitability = 0.0

    @api.depends('standard_price', 'taxes_id')
    def _compute_prices(self):
        for product in self:
            iva = 0
            # Solo considerar el primer impuesto
            if product.taxes_id:
                tax = product.taxes_id[0]
                tax_name = tax.name.lower()
                if '19' in tax_name:
                    iva = 19
                elif '5' in tax_name:
                    iva = 5
                elif '0' in tax_name:
                    iva = 0
                else:
                    iva = 0  # Si no coincide con 19, 5 o 0, se ignora

            # Cálculo de precios con IVA y descuento
            product.price_10 = product.standard_price / ((100 - 10) / 100) * ((1 + (iva / 100)))
            product.price_15 = product.standard_price / ((100 - 15) / 100) * ((1 + (iva / 100)))
            product.price_20 = product.standard_price / ((100 - 20) / 100) * ((1 + (iva / 100)))
            product.price_30 = product.standard_price / ((100 - 30) / 100) * ((1 + (iva / 100)))
            product.price_40 = product.standard_price / ((100 - 40) / 100) * ((1 + (iva / 100)))
            product.price_50 = product.standard_price / ((100 - 50) / 100) * ((1 + (iva / 100)))
            
    @api.onchange('standard_price')
    def _onchange_standard_price(self):
        self._compute_prices()

