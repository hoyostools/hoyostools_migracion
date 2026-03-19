from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    importable = fields.Boolean()
    is_free = fields.Boolean()
    company_ids = fields.Char()
    manufacturer_id = fields.Integer()
    product_manufacturer = fields.Char()
    manufacturer_pname = fields.Char()
    manufacturer_pref = fields.Char()
    manufacturer_purl = fields.Char()
    warranty = fields.Integer()
    warranty_type = fields.Char()
    last_purchase_supplier_id = fields.Char()
    product_type_id = fields.Integer()
    arancel_ids = fields.Char()
    model_id = fields.Integer()
    last_purchase_date = fields.Date()
    last_purchase_price = fields.Float()
    show_last_purchase_price_currency = fields.Boolean()
    last_purchase_currency_id = fields.Char()
    srv_type = fields.Char()
    last_purchase_price_currency = fields.Float()
    taxes_updeatable_from_category = fields.Boolean()
    tariff_id = fields.Integer()
    sale_price_history_ids = fields.Char()