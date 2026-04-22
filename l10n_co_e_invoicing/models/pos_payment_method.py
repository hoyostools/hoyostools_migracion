from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    account_payment_mean = fields.Many2one('account.payment.mean',string='Metodo de pago')