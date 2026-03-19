
from odoo import models, fields

class ProductividadTurno(models.Model):
    _name = 'productividad.turno'
    _description = 'Configuración de Turnos'

    name = fields.Char(string='Nombre', required=True)
    codigo = fields.Selection([
        ('1', 'Turno 1'),
        ('2', 'Turno 2'),
        ('3', 'Turno 3'),
        ('adicional', 'Adicional')
    ], required=True)

    hora_inicio = fields.Float(string='Hora Inicio', required=True)
    hora_fin = fields.Float(string='Hora Fin', required=True)

    activo = fields.Boolean(default=True)