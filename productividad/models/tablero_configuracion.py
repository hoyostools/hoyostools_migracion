from odoo import models, fields

class TableroConfiguracion(models.Model):
    _name = 'productividad.tablero_configuracion'
    _description = 'Tablero de Configuración de Usuarios'

    user_id = fields.Many2one('res.users', string="Usuario Interno", required=True)
    funcion = fields.Selection([
        ('empacador', 'Empacador'),
        ('separador', 'Separador'),
        ('montacarguista', 'Montacarguista'),
    ], string="Función", required=True)
    turno_id = fields.Many2one(
        'productividad.turno',
        string="Turno",
        required=True
    )
    
    combo_pasillo_id = fields.Many2one('productividad.combo_pasillo', string="Combo de Pasillo",
        domain="[('id', '!=', False)]")
