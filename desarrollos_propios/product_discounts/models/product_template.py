from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    descuento_1 = fields.Float(
        string="Descuento 1",
        compute='_compute_descuentos',
        store=False
    )
    descuento_2 = fields.Float(
        string="Descuento 2",
        compute='_compute_descuentos',
        store=False
    )
    descuento_3 = fields.Float(
        string="Descuento 3",
        compute='_compute_descuentos',
        store=False
    )

    def _compute_descuentos(self):
        Pricelist = self.env['product.pricelist']
        PricelistItem = self.env['product.pricelist.item']

        # Obtener las listas de precios relevantes
        pricelists = Pricelist.search([
            ('name', 'in', ['Descuento Adicional', 'Evento Descuento 1', 'Evento Descuento 2'])
        ])
        pricelist_map = {pl.name: pl.id for pl in pricelists}

        # Buscar todas las reglas asociadas
        items = PricelistItem.search([
            ('pricelist_id', 'in', list(pricelist_map.values())),
        ])

        # Agrupar por lista de precios
        grouped_items = {}
        for item in items:
            grouped_items.setdefault(item.pricelist_id.id, []).append(item)

        for product in self:
            product.descuento_1 = self._get_discount_by_priority(product, grouped_items.get(pricelist_map.get('Descuento Adicional'), []))
            product.descuento_2 = self._get_discount_by_priority(product, grouped_items.get(pricelist_map.get('Evento Descuento 1'), []))
            product.descuento_3 = self._get_discount_by_priority(product, grouped_items.get(pricelist_map.get('Evento Descuento 2'), []))

    def _get_discount_by_priority(self, product, items):
        """
        Jerarquía:
        1) variante  2) plantilla  3) categoría  4) global
        5) marca     6) país origen 7) etiqueta
        """
        # 1) Variante (product.product)
        for it in items:
            if it.applied_on == '0_product_variant' and it.product_id and it.product_id.product_tmpl_id == product:
                return it.price_discount

        # 2) Producto (plantilla)
        for it in items:
            if it.applied_on == '1_product' and it.product_tmpl_id == product:
                return it.price_discount

        # 3) Categoría
        for it in items:
            if it.applied_on == '2_product_category' and it.categ_id == product.categ_id:
                return it.price_discount

        # 4) Global
        for it in items:
            if it.applied_on == '3_global':
                return it.price_discount

        # 5) Marca
        for it in items:
            if (
                it.applied_on == '4_product_brand' 
                and it.apply_brand
                and getattr(product, 'product_brand_id', False) 
                and it.apply_brand.id == product.product_brand_id.id
            ):        
                return it.price_discount
            
        # 6) País de origen
        for it in items:
            if (
                it.applied_on == '5_product_origin_country'
                and it.apply_origin_country
                and product.country_of_origin
                and it.apply_origin_country.id == product.country_of_origin.id
            ):
                return it.price_discount

        # 7) Etiqueta
        for it in items:
            
            if (
                it.applied_on == '6_product_tag' 
                and it.apply_tag 
                and product.product_tag_ids 
                and set(it.apply_tag.ids).intersection(product.product_tag_ids.ids)
            ):
                return it.price_discount

        return 0.0

