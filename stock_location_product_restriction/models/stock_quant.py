# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.constrains("location_id", "product_id")
    def _check_location_product_restriction(self):
        """
        Verifica si la cantidad se puede colocar en la ubicación según la restricción definida en stock_location.

        Nota funcional (Odoo 17):
        Para la restricción 'same', una ubicación debe considerarse "ocupada" únicamente si tiene
        cantidad física (quantity) > 0. Reservas (reserved_quantity) o conteos (inventory_quantity)
        no deben impedir reabastecer una ubicación físicamente vacía.
        """
        StockLocation = self.env["stock.location"]
        ProductProduct = self.env["product.product"]

        quants_to_check = self.filtered(lambda q: q.location_id.product_restriction == "same")
        if not quants_to_check:
            return

        product_ids_location_id = defaultdict(set)
        error_msgs = []

        # 1) Validar que no se intenten meter dos productos distintos a la vez en la misma ubicación
        for quant in quants_to_check:
            product_ids_location_id[quant.location_id.id].add(quant.product_id.id)

        for location_id, product_ids in product_ids_location_id.items():
            if len(product_ids) > 1:
                location = StockLocation.browse(location_id)
                products = ProductProduct.browse(list(product_ids))
                error_msgs.append(
                    _(
                        "La ubicación %(location)s solo puede contener elementos del mismo "
                        "producto. Planeas poner diferentes productos en "
                        "esta ubicación. (%(products)s)",
                        location=location.name,
                        products=", ".join(products.mapped("name")),
                    )
                )

        # 2) Obtener el/los productos físicamente presentes en la ubicación (SOLO quantity)
        precision_digits = max(
            6, self.sudo().env.ref("product.decimal_product_uom").digits * 2
        )

        # Agregado el 22 - 01 - 2026
        self.flush_model(["product_id", "location_id", "quantity"])
        SQL = """
            SELECT
                location_id,
                array_agg(distinct(product_id))
            FROM
                stock_quant
            WHERE
                location_id in %s
                AND NOT (round(quantity::numeric, %s) = 0 OR quantity IS NULL)
            GROUP BY
                location_id
        """
        # Agregado el 22 - 01 - 2026
        self.env.cr.execute(
            SQL,
            (
                tuple(quants_to_check.mapped("location_id").ids),
                precision_digits,
            ),
        )
        existing_product_ids_by_location_id = dict(self.env.cr.fetchall())

        # 3) Validar: si la ubicación tiene stock físico de un producto distinto, bloquear
        for location_id, existing_product_ids in existing_product_ids_by_location_id.items():
            product_ids_to_add = product_ids_location_id[location_id]

            # Si en la ubicación hay stock físico de otro producto, no permitir
            if set(existing_product_ids).symmetric_difference(product_ids_to_add):
                location = StockLocation.browse(location_id)
                existing_products = ProductProduct.browse(existing_product_ids)
                to_move_products = ProductProduct.browse(list(product_ids_to_add))
                error_msgs.append(
                    _(
                        "Planeas agregar el producto %(product)s hacia el lugar %(location)s "
                        "pero la ubicación debe contener solo elementos del mismo tipo "
                        "producto y ya contiene artículos de otros product(s) "
                        "(%(existing_products)s).",
                        product=" | ".join(to_move_products.mapped("name")),
                        location=location.name,
                        existing_products=" | ".join(existing_products.mapped("name")),
                    )
                )

        if error_msgs:
            raise ValidationError("\n".join(error_msgs))