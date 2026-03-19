from odoo import fields, models, api, _

class StockLocation(models.Model):

    _inherit = 'stock.location'

    funcion = fields.Selection(string="Funciones", selection=[('bodegaje', 'Bodegaje'),
                                                              ('pasillo01', 'Pasillo 01'),
                                                              ('pasillo02', 'Pasillo 02'),
                                                              ('pasillo03', 'Pasillo 03'),
                                                              ('pasillo04', 'Pasillo 04'),
                                                              ('pasillo05', 'Pasillo 05'),
                                                              ('pasillo06', 'Pasillo 06'),
                                                              ('pasillo07', 'Pasillo 07'),
                                                              ('pasillo08', 'Pasillo 08'),
                                                              ('pasillo09', 'Pasillo 09'),
                                                              ('pasillo10', 'Pasillo 10'),
                                                              ('pasillo11', 'Pasillo 11'),
                                                              ('pasillo12', 'Pasillo 12'),
                                                              ('piso01', 'Piso 01'),
                                                              ('piso02', 'Piso 02'),
                                                              ('piso03', 'Piso 03'),
                                                              ('piso04', 'Piso 04'),
                                                              ('piso05', 'Piso 05'), ])