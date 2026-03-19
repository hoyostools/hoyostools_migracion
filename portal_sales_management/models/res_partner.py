from odoo import models, fields, api, tools, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_seller = fields.Boolean(
        string='Vendedor',
        required=False)

    # sale_user_id = fields.Many2one('res.users')
