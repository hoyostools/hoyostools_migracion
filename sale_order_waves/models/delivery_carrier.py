from odoo import fields, models, api, _

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tipo = fields.Selection(string="Tipo", selection=[('ruta', 'Ruta'),
                                                      ('horas', '24 Horas'),
                                                      ('despacho', 'Despacho'),
                                                      ('flex', 'FLEX'),
                                                      ('mkp', 'Marketplace'),
                                                      ('pos', 'POS'),
                                                      ('recogen', 'Recogen Edificio')])