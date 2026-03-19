from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    contacto = fields.Many2one(
        "res.partner",
        string="Contacto",
    )

    @api.model_create_multi
    def create(self, vals_list):
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        # Obtener todos los move_ids involucrados (optimización)
        move_ids = {
            vals.get("move_id")
            for vals in vals_list
            if isinstance(vals, dict) and vals.get("move_id")
        }

        moves = self.env["account.move"].browse(move_ids)
        move_map = {move.id: move for move in moves}

        for vals in vals_list:
            if not isinstance(vals, dict):
                continue

            move_id = vals.get("move_id")
            contacto = vals.get("contacto")

            if not move_id or not contacto:
                continue

            move = move_map.get(move_id)

            # SOLO factura proveedor
            if move and move.move_type == "in_invoice":
                vals["partner_id"] = contacto

        return super().create(vals_list)

    def write(self, vals):
        if "contacto" in vals:
            for line in self:
                if (
                    line.move_id.move_type == "in_invoice"
                    and vals.get("contacto")
                ):
                    vals["partner_id"] = vals["contacto"]

        return super().write(vals)

    def _compute_tax_lines(self):
        for line in self:
            if (
                line.move_id.move_type == "in_invoice"
                and line.contacto
            ):
                line = line.with_context(force_contacto=line.contacto.id)

        return super()._compute_tax_lines()

class AccountTax(models.Model):
    _inherit = "account.tax"

    def _compute_all(
        self, price_unit, currency=None, quantity=1.0,
        product=None, partner=None, is_refund=False,
        handle_price_include=True, include_caba_tags=False
    ):
        if self.env.context.get("force_contacto"):
            partner = self.env["res.partner"].browse(
                self.env.context["force_contacto"]
            )

        return super()._compute_all(
            price_unit,
            currency=currency,
            quantity=quantity,
            product=product,
            partner=partner,
            is_refund=is_refund,
            handle_price_include=handle_price_include,
            include_caba_tags=include_caba_tags,
        )
