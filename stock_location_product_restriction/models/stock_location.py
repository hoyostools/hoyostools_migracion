# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.osv.expression import NEGATIVE_TERM_OPERATORS


class StockLocation(models.Model):
    _inherit = "stock.location"

    product_restriction = fields.Selection(
        selection=lambda self: self._selection_product_restriction(),
        string="Restricción de producto",
        help=(
            "Si se selecciona 'Mismo producto', el sistema impedirá "
            "almacenar artículos de diferentes productos en la misma ubicación."
        ),
        index=True,
        required=True,
        compute="_compute_product_restriction",
        store=True,
        default="any",
        recursive=True,
    )

    specific_product_restriction = fields.Selection(
        selection=lambda self: self._selection_product_restriction(),
        string="Restricción específica de producto",
        help=(
            "Si se especifica, esta restricción se aplicará a la ubicación "
            "actual y a todas sus ubicaciones secundarias."
        ),
        default=False,
    )

    parent_product_restriction = fields.Selection(
        string="Restricción de Producto por Ubicación Principal",
        store=True,
        readonly=True,
        related="location_id.product_restriction",
        recursive=True,
    )

    has_restriction_violation = fields.Boolean(
        string="Violación de restricción",
        compute="_compute_restriction_violation",
        search="_search_has_restriction_violation",
        recursive=True,
    )

    restriction_violation_message = fields.Char(
        compute="_compute_restriction_violation",
        recursive=True,
    )

    @api.model
    def _selection_product_restriction(self):
        return [
            ("any", "Se permiten artículos de cualquier producto en el lugar"),
            ("same", "Solo se permiten artículos del mismo producto en la ubicación"),
        ]

    @api.depends("specific_product_restriction", "parent_product_restriction")
    def _compute_product_restriction(self):
        default_value = "any"
        for rec in self:
            rec.product_restriction = (
                rec.specific_product_restriction
                or rec.parent_product_restriction
                or default_value
            )


    #Agregado el 22 - 01 - 2026
    @api.depends("product_restriction")
    def _compute_restriction_violation(self):
        """
        (A) Consistencia con el constraint de stock_quant:
        Para restricción 'same', la "ocupación" de la ubicación se determina
        únicamente por cantidad física (quantity > 0).
        Reservas (reserved_quantity) o conteos (inventory_quantity) no cuentan
        como contenido físico para esta regla.
        """
        records = self
        self.env["stock.quant"].flush_model(
            ["product_id", "location_id", "quantity"]
        )
        self.flush_model(["product_restriction"])

        ProductProduct = self.env["product.product"]
        precision_digits = max(
            6, self.sudo().env.ref("product.decimal_product_uom").digits * 2
        )

        SQL = """
           SELECT
               stock_quant.location_id,
               array_agg(distinct(stock_quant.product_id))
           FROM
               stock_quant,
               stock_location
           WHERE
               stock_quant.location_id in %s
               AND stock_location.id = stock_quant.location_id
               AND stock_location.product_restriction = 'same'
               AND NOT (round(stock_quant.quantity::numeric, %s) = 0 OR stock_quant.quantity IS NULL)
           GROUP BY
               stock_quant.location_id
           HAVING count(distinct(stock_quant.product_id)) > 1
       """

        # Browse only real record ids
        ids = tuple(
            [record.id for record in records if not isinstance(record.id, fields.NewId)]
        )
        if not ids:
            product_ids_by_location_id = {}
        else:
            self.env.cr.execute(SQL, (ids, precision_digits))
            product_ids_by_location_id = dict(self.env.cr.fetchall())

        for record in self:
            record_id = record.id
            has_restriction_violation = False
            restriction_violation_message = False

            product_ids = product_ids_by_location_id.get(record_id)
            if product_ids:
                products = ProductProduct.browse(product_ids)
                has_restriction_violation = True
                restriction_violation_message = _(
                    "Esta ubicación solo debe contener artículos del mismo tipo "
                    "producto pero contiene artículos de productos %(products)s",
                    products=" | ".join(products.mapped("name")),
                )

            record.has_restriction_violation = has_restriction_violation
            record.restriction_violation_message = restriction_violation_message

    def _search_has_restriction_violation(self, operator, value):
        """
        (B) Búsqueda consistente con (A): solo quantity define ocupación física.
        """
        precision_digits = max(
            6, self.sudo().env.ref("product.decimal_product_uom").digits * 2
        )
        search_has_violation = (
            (operator in NEGATIVE_TERM_OPERATORS and not value)
            or (operator not in NEGATIVE_TERM_OPERATORS and value)
        )

        self.env["stock.quant"].flush_model(["product_id", "location_id", "quantity"])
        self.flush_model(["product_restriction"])

        SQL = """
            SELECT
                stock_quant.location_id
            FROM
               stock_quant,
               stock_location
            WHERE
               stock_location.id = stock_quant.location_id
               AND stock_location.product_restriction = 'same'
               AND NOT (round(stock_quant.quantity::numeric, %s) = 0 OR stock_quant.quantity IS NULL)
            GROUP BY
               stock_quant.location_id
            HAVING count(distinct(stock_quant.product_id)) > 1
        """
        self.env.cr.execute(SQL, (precision_digits,))
        violation_ids = [r[0] for r in self.env.cr.fetchall()]

        op = "in" if search_has_violation else "not in"
        return [("id", op, violation_ids)]
    # Agregado el 22 - 01 - 2026