from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    financial_discount_percentage = fields.Float(
        string='% Descuento Financiero',
        store=True
    )
    maximum_date_financial_discount = fields.Integer(string="Días Máximo para Descuento Financiero", store=True)