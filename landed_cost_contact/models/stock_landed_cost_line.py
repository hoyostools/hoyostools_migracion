from odoo import models, fields, api


class StockLandedCostLine(models.Model):
    _inherit = "stock.landed.cost.lines"

    contact_id = fields.Many2one(
        "res.partner",
        string="Contacto",
    )

    allowed_contact_ids = fields.Many2many(
        "res.partner",
        compute="_compute_allowed_contacts",
    )

    @api.depends("product_id")
    def _compute_allowed_contacts(self):

        for line in self:

            if line.product_id:
                line.allowed_contact_ids = line.product_id.product_tmpl_id.landed_cost_contact_ids
            else:
                line.allowed_contact_ids = False

            if line.contact_id and line.contact_id not in line.allowed_contact_ids:
                line.contact_id = False