from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductividadComboPasillo(models.Model):
    _name = 'productividad.combo_pasillo'
    _description = 'Combo de Pasillos'

    name = fields.Char(string='Nombre', required=True)
    pasillo_inicio = fields.Integer(string='Del Pasillo', required=True)
    pasillo_fin = fields.Integer(string='Al Pasillo')
    documentos = fields.Integer(string='Documentos', required=True)
    items = fields.Integer(string='Items', required=True)
    puntos = fields.Float(string='Puntos', required=True)

    @api.constrains('pasillo_inicio', 'pasillo_fin')
    def _check_pasillo_range(self):
        for record in self:
            if record.pasillo_fin and record.pasillo_inicio > record.pasillo_fin:
                raise ValidationError("El pasillo de inicio no puede ser mayor al pasillo final.")
            if record.pasillo_inicio < 1 or (record.pasillo_fin and record.pasillo_fin > 20):
                raise ValidationError("El rango de pasillos debe estar entre 1 y 20.")

    @api.constrains('pasillo_inicio', 'pasillo_fin')
    def _check_unique_pasillos(self):
        for record in self:
            used_pasillos = set()
            combos = self.search([('id', '!=', record.id)])
            for combo in combos:
                start = combo.pasillo_inicio
                end = combo.pasillo_fin or combo.pasillo_inicio
                used_pasillos.update(range(start, end + 1))

            current_range = set(range(record.pasillo_inicio, (record.pasillo_fin or record.pasillo_inicio) + 1))
            if used_pasillos.intersection(current_range):
                raise ValidationError("Los pasillos seleccionados ya están asignados a otro combo.")
