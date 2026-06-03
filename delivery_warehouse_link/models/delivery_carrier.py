from odoo import models, fields, api

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Almacén',
        domain=lambda self: [('company_id', '=', self.env.company.id)],
    )
