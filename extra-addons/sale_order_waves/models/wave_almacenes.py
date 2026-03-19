from odoo import fields, models, api, _

class WaveAlmacenes(models.Model):
    _name = 'wave.almacenes'

    almacen = fields.Many2one('stock.warehouse', string='Almacén')