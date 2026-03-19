from odoo import models, fields, api

class ConfiguracionMeta(models.Model):
    _name = 'productividad.configuracion_meta'
    _description = 'Configuración de Metas Diarias'

    nombre = fields.Char(string="Nombre de la Meta", required=True)
    proceso = fields.Selection([
        ('picking', 'Picking'),
        ('packing', 'Packing'),
        ('almacenamiento', 'Almacenamiento')
    ], string="Proceso", required=True)
    fecha_inicio = fields.Date(string="Desde", required=True)
    fecha_fin = fields.Date(string="Hasta", required=True)
    
    meta_items_diarios = fields.Integer(string="Meta Items Diarios", required=True)
    meta_documentos_diarios = fields.Integer(string="Meta Documentos Diarios", required=True)
    meta_puntos_diarios = fields.Float(string="Meta Puntos Diarios", required=True, help="1 punto equivale a 1,000,000")
    
    porcentaje_items = fields.Float(string="% Part Items")
    porcentaje_documentos = fields.Float(string="% Part Doc")
    porcentaje_puntos = fields.Float(string="% Part Puntos")

    def nombre_get(self):
        return [(rec.id, f"{rec.nombre} - {rec.mes}") for rec in self]


    @api.model
    def get_meta_for_date(self, proceso, fecha):
        domain = [
            ('proceso', '=', proceso),
            ('fecha_inicio', '<=', fecha),
            ('fecha_fin', '>=', fecha),
        ]
        return self.search(domain, order='fecha_inicio desc', limit=1)