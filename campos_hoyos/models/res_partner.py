from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    # def create(self, vals):
    #     res = super(ResPartner, self).create(vals)
    #     if not res.company_type and res.l10n_latam_identification_type_id.name == 'NIT':
    #         res.company_type = 'company'
    #     elif not res.company_type and res.l10n_latam_identification_type_id.name == 'Cédula de ciudadanía':
    #         res.company_type = 'person'
    #     if not res.organization_type_id and res.company_type == 'company':
    #         res.organization_type_id = self.env["dian.companytype"].search([("name", "=", "Persona Juridica")])
    #     elif not res.organization_type_id and res.company_type == 'person':
    #         res.organization_type_id = self.env["dian.companytype"].search([("name", "=", "Persona Natural")])
    #     if not res.city_id:
    #         res.city_id = self.env["res.city"].search([("name", "=", "CALI")])
    #     return res

    property_payment_term_id = fields.Many2one('account.payment.term', company_dependent=True,
                                               string='Customer Payment Terms',
                                               help="This payment term will be used instead of the default one for sales orders and customer invoices", tracking = True)

    property_product_pricelist = fields.Many2one(
        comodel_name='product.pricelist',
        string="Pricelist",
        compute='_compute_product_pricelist',
        inverse="_inverse_product_pricelist",
        company_dependent=False,
        domain=lambda self: [('company_id', 'in', (self.env.company.id, False))],
        help="This pricelist will be used, instead of the default one, for sales to the current partner", tracking = True)

    property_delivery_carrier_id = fields.Many2one('delivery.carrier', company_dependent=True, string="Delivery Method",
                                                   help="Default delivery method used in sales orders.", tracking = True)