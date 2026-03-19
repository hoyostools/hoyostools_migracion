from odoo import models, fields

class StockLocation(models.Model):
    _inherit = 'stock.location'

    tunel = fields.Selection([
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('PKM1', 'PKM1'),
        ('PKM2', 'PKM2'),
        ('A2', 'A2'),
        ('B2', 'B2'),
        ('C2', 'C2'),
        ('D2', 'D2'),
    ], string='Túnel')