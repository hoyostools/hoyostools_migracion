from odoo import fields, models, api
from odoo.exceptions import ValidationError


class SaleMontacargas(models.Model):
    _name = 'sale.montacargas'

    activo = fields.Boolean(string='Activo', default=False)
    user_id = fields.Many2one('res.users', string="Usuario")
    image_1920 = fields.Image(related="user_id.image_1920",string="Imagen", max_width=1920, max_height=1920)
    funcion = fields.Selection(string="Funciones", selection=[('montacargas', 'Montacargas'),
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
                                                              ('piso05', 'Piso 05'),
                                                              ('piso04', 'Piso 04'),
                                                              ('turbo', 'Turbo'),
                                                              ('flex', 'FLEX'),
                                                              ('mkp', 'MKP'),
                                                              ('empaque', 'EMPAQUE'),
                                                              ('turbo_empaque', 'Turbo-Empaque'),
                                                              ('flex_empaque', 'Flex-Empaque'),
                                                              ('mkp_empaque', 'MKP-Empaque')])
    asignaciones = fields.Integer(string='Asignaciones', default=False)
