from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def default_get(self, fields_list):
        # Obtiene valores predeterminados
        values = super().default_get(fields_list)
        # Asigna la compañía actual como valor predeterminado para `company_ids`
        if 'company_ids' in fields_list:
            values['company_ids'] = [(6, 0, [self.env.company.id])]
        return values

    def create(self, values):
        # Obtén la compañía actual
        company = self.env.company

        # Verifica si values es una lista (batch creation)
        if isinstance(values, list):
            for val in values:
                if 'company_ids' not in val and not company.is_main:
                    val['company_ids'] = [(6, 0, [company.id])]
        else:
            # Caso para un solo diccionario
            if 'company_ids' not in values and not company.is_main:
                values['company_ids'] = [(6, 0, [company.id])]

        return super(ProductTemplate, self).create(values)



