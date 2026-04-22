from odoo import api, fields, models

class ResBank(models.Model):

    _inherit = "res.bank"

    document_type_bank_id = fields.Many2one('res.partner.document.type', string="Document Type")
    identification_document_bank = fields.Char(string="Identification Document")
    check_digit_bank = fields.Char(string="Check Digit")
