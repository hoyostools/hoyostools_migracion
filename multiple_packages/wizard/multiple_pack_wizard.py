# Copyright 2026 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import math

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MultiplePackWizard(models.TransientModel):
    """Split one stock move line into multiple packages.

    The wizard supports two input modes:
    - Provide *Number of packages*: total quantity is distributed as evenly as possible.
      Any remainder is added to the first packages
      (e.g. 5 qty into 2 packages -> [3, 2]).
    - Provide *Items per package*: create full packages plus the last remainder package.
    """

    _name = "multiple.pack.wizard"
    _description = "Wizard: Multiple Packages"

    move_line_id = fields.Many2one(
        "stock.move.line",
        required=True,
    )

    package_type_id = fields.Many2one(
        "stock.package.type",
        string="Package Type",
    )

    has_carrier = fields.Boolean(readonly=True)
    items_per_package = fields.Integer(default=0)
    number_of_packages = fields.Integer(default=1)
    quantity_total = fields.Float(readonly=True)

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if "has_carrier" in fields_list:
            values["has_carrier"] = bool(self.env.context.get("has_carrier"))
        return values

    def action_pack(self):
        self.ensure_one()
        self._validate_inputs()

        source_move_line = self.move_line_id
        package_quantities = self._compute_package_quantities()

        packages = self._create_packages(len(package_quantities))
        self._split_move_line_into_packages(
            source_move_line=source_move_line,
            packages=packages,
            quantities=package_quantities,
        )

        if self.has_carrier:
            return self._open_package_details_wizard(packages)

        if self.package_type_id:
            packages.write({"package_type_id": self.package_type_id.id})

        return {"type": "ir.actions.act_window_close"}

    def _validate_inputs(self):
        self.ensure_one()

        total_qty = int(self.quantity_total or 0)
        if total_qty <= 0:
            raise UserError(_("Total quantity must be greater than zero."))

        has_number_of_packages = bool(self.number_of_packages)
        has_items_per_package = bool(self.items_per_package)

        if has_number_of_packages and has_items_per_package:
            raise UserError(
                _(
                    "Fill either Number of packages OR Items per package "
                    "(only one)."
                )
            )

        if not has_number_of_packages and not has_items_per_package:
            raise UserError(
                _("You must fill either Number of packages or Items per package.")
            )

        if has_number_of_packages and self.number_of_packages <= 0:
            raise UserError(_("Number of packages must be greater than zero."))

        if has_items_per_package and self.items_per_package <= 0:
            raise UserError(_("Items per package must be greater than zero."))

    def _compute_package_quantities(self):
        """Return a list of quantities to put into each package."""
        self.ensure_one()

        total_qty = int(self.quantity_total or 0)
        if total_qty <= 0:
            return []

        if self.number_of_packages:
            packages_count = int(self.number_of_packages)

            # If quantity is smaller than the number of packages, create one item
            # per package (limited by quantity).
            if packages_count >= total_qty:
                return [1] * total_qty

            base_qty = total_qty // packages_count
            remainder = total_qty % packages_count

            # Distribute the remainder to the first packages.
            return (
                [base_qty + 1] * remainder
                + [base_qty] * (packages_count - remainder)
            )

        items_per_package = int(self.items_per_package)
        packages_count = int(math.ceil(total_qty / float(items_per_package)))
        last_package_qty = total_qty - items_per_package * (packages_count - 1)

        return [items_per_package] * (packages_count - 1) + [last_package_qty]

    def _create_packages(self, count):
        Package = self.env["stock.quant.package"]
        packages = Package.browse()
        for _i in range(count):
            packages |= Package.create({})
        return packages

    def _split_move_line_into_packages(self, source_move_line, packages, quantities):
        """Split the source move line and assign each part to a package."""
        if not quantities:
            return

        # Update the original move line with the first quantity.
        source_move_line.write(
            {"quantity": quantities[0], "result_package_id": packages[0].id}
        )

        # Create additional move lines for the remaining packages.
        for index in range(1, len(quantities)):
            source_move_line.copy(
                {"quantity": quantities[index], "result_package_id": packages[index].id}
            )

    def _open_package_details_wizard(self, packages):
        self.ensure_one()
        carrier = self.move_line_id.picking_id.carrier_id
        carrier_package_type = carrier.delivery_type if carrier else False

        return {
            "name": _("Package Details"),
            "type": "ir.actions.act_window",
            "res_model": "multiple.pack.package.details.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_package_id": packages[0].id,
                "default_remaining_package_ids": packages[1:].ids,
                "carrier_package_type": carrier_package_type,
            },
        }
