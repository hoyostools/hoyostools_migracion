from odoo import fields, models

class CustomIdentificationType(models.Model):
    _inherit = 'l10n_latam.identification.type'

    dian_code = fields.Selection([
        ('11', 'Registro civil'),
        ('12', 'Tarjeta de identidad'),
        ('13', 'Cédula de ciudadanía'),
        ('21', 'Tarjeta de extranjería'),
        ('22', 'Cédula de extranjería'),
        ('31', 'NIT'),
        ('41', 'Pasaporte'),
        ('42', 'Documento de identificación extranjero'),
        ('47', 'PEP'),
        ('50', 'NIT de otro país'),
        ('91', 'NUIP')
    ], string="Código DIAN")
