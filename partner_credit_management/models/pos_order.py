from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_res_partner(self):
        result = super()._loader_params_res_partner()

        fields = result['search_params']['fields']

        if 'credit_blocked' not in fields:
            fields.append('credit_blocked')

        return result