from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_main = fields.Boolean(string='Compañia principal')
    stock_hoyos = fields.Boolean(string='Mostrar inventario de Hoyos')

    @api.constrains('is_main')
    def _check_main_company(self):
        for record in self:
            if record.is_main:
                # Buscamos si hay otra empresa marcada como principal
                other_main_companies = self.search([('id', '!=', record.id), ('is_main', '=', True)])
                if other_main_companies:
                    raise ValidationError("Solo puede haber una compañía principal.")

