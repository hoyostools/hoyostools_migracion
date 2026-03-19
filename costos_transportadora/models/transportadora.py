from odoo import models, fields


class Transportadora(models.Model):
    _name = 'transportadora.transportadora'
    _description = 'Transportadoras'

    name = fields.Char(string='Nombre', required=True)
