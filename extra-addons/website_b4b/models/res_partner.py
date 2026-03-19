from odoo import api, fields, models 


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def create(self, values):
        company = self.env.company
        if not company.is_main:
            if isinstance(values, list):
                for value in values:
                    value['company_id'] = company.id
            else:
                values['company_id'] = company.id
        return super(ResPartner, self).create(values)

