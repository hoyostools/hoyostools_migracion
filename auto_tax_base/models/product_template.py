from odoo import api, models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    no_validar_bases = fields.Boolean(string='No Validar Impuestos', default=False)

    def create(self,vals):
        if 'supplier_taxes_id' not in vals:
            vals['no_validar_bases'] = True
        return super().create(vals)

    def write(self,vals):
        res = super().write(vals)
        if not res.supplier_taxes_id:
            res.no_validar_bases = True
        return res