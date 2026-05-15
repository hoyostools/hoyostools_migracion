from odoo import models, fields


class ApAnticipo(models.Model):
    _name = "ap.anticipo"
    _description = "Customer Advance Configuration"
    _rec_name = "name"

    name = fields.Char(
        string="Name",
        required=True
    )

    cuenta_anticipo_id = fields.Many2one(
        comodel_name="account.account",
        string="Cuenta de anticipo",
        domain="[('account_type', 'in', ('asset_receivable', 'liability_payable'))]",
        required=True
    )

    internal_type_id = fields.Selection(
        related="cuenta_anticipo_id.account_type",
        string="Tipo Interno",
        readonly=True,
        store=True
    )