from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = "account.payment"

    tipo_anticipo_id = fields.Many2one(
        comodel_name="ap.anticipo",
        string="Tipo de anticipo"
    )

    anticipo = fields.Boolean(
        string="Anticipo"
    )