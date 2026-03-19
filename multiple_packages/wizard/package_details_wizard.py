# Copyright 2026 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import _, api, fields, models


class MultiplePackPackageDetailsWizard(models.TransientModel):
    """Wizard to set package type and shipping weight for multiple packages."""

    _name = "multiple.pack.package.details.wizard"
    _description = "Wizard: Package Details"

    package_id = fields.Many2one("stock.quant.package", required=True)
    package_name = fields.Char(
        string="Name",
        related="package_id.display_name",
        readonly=True,
    )

    company_id = fields.Many2one(
        "res.company",
        readonly=True,
        default=lambda self: self.env.company,
    )

    package_type_id = fields.Many2one("stock.package.type", string="Package Type")
    shipping_weight = fields.Float(
        string="Weight",
        compute="_compute_shipping_weight",
        store=True,
        readonly=False,
    )
    weight_uom_name = fields.Char(
        string="Weight UoM",
        compute="_compute_weight_uom_name",
    )

    remaining_package_ids = fields.Many2many(
        "stock.quant.package",
        string="Remaining Packages",
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)

        remaining_ids = self.env.context.get("default_remaining_package_ids")
        if remaining_ids and "remaining_package_ids" in fields_list:
            values["remaining_package_ids"] = [(6, 0, remaining_ids)]

        return values

    @api.depends("package_type_id")
    def _compute_weight_uom_name(self):
        weight_uom = (
            self.env["product.template"]
            ._get_weight_uom_id_from_ir_config_parameter()
        )
        for wizard in self:
            wizard.weight_uom_name = weight_uom.name

    @api.depends("package_type_id", "package_id")
    def _compute_shipping_weight(self):
        for wizard in self:
            wizard.shipping_weight = wizard._calculate_package_weight()

    def _calculate_package_weight(self):
        self.ensure_one()

        base_weight = self.package_type_id.base_weight or 0.0
        total_weight = base_weight

        move_lines = self.env["stock.move.line"].search(
            [("result_package_id", "=", self.package_id.id)]
        )
        for move_line in move_lines:
            qty_in_product_uom = move_line.product_uom_id._compute_quantity(
                move_line.quantity,
                move_line.product_id.uom_id,
            )
            total_weight += qty_in_product_uom * (move_line.product_id.weight or 0.0)

        return total_weight

    def _apply_to_package(self):
        self.ensure_one()

        if not self.package_type_id:
            return

        self.package_id.write(
            {
                "package_type_id": self.package_type_id.id,
                "shipping_weight": self.shipping_weight,
            }
        )

    def action_next(self):
        self.ensure_one()
        self._apply_to_package()

        remaining = self._order_packages(self.remaining_package_ids)
        if not remaining:
            return {"type": "ir.actions.act_window_close"}

        next_package = remaining[0]
        next_remaining_ids = remaining[1:].ids

        ctx = dict(self.env.context)
        ctx.update(
            {
                "default_package_id": next_package.id,
                "default_remaining_package_ids": next_remaining_ids,
            }
        )

        return {
            "name": _("Package Details"),
            "type": "ir.actions.act_window",
            "res_model": "multiple.pack.package.details.wizard",
            "view_mode": "form",
            "target": "new",
            "context": ctx,
        }

    def action_finish(self):
        self.ensure_one()
        self._apply_to_package()
        return {"type": "ir.actions.act_window_close"}

    def _order_packages(self, packages):
        """Return packages ordered in a stable way.

        Some code paths may pass records with NewId (unsaved ids), which breaks
        sorting by ``id``. This helper sorts with a safe key that works for both
        saved and unsaved records.
        """

        def _key(package):
            pkg_id = package.id
            if isinstance(pkg_id, int):
                return pkg_id

            origin = getattr(package, "_origin", None)
            origin_id = getattr(origin, "id", 0)
            return origin_id if isinstance(origin_id, int) else 0

        return packages.sorted(key=_key)
