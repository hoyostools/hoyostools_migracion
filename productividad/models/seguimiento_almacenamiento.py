from odoo import models, fields, api

class SeguimientoAlmacenamiento(models.Model):
    _name = 'productividad.seguimiento_almacenamiento'
    _description = 'Seguimiento Diario de Almacenamiento'

    user_id = fields.Many2one('res.users', string="Nombre del Operario")
    fecha = fields.Date(string="Fecha")
    items = fields.Integer(string="Items")
    documentos = fields.Integer(string="Documentos")
    puntos = fields.Float(string="Puntos")

    cumplimiento_items = fields.Float(string="C. Items %", compute="_compute_cumplimientos", store=False)
    cumplimiento_documentos = fields.Float(string="C. Documentos %", compute="_compute_cumplimientos", store=False)
    cumplimiento_puntos = fields.Float(string="C. Puntos %", compute="_compute_cumplimientos", store=False)

    meta_items_diarios = fields.Integer(string="Meta Items", compute="_compute_metas", store=False)
    meta_documentos_diarios = fields.Integer(string="Meta Documentos", compute="_compute_metas", store=False)
    meta_puntos_diarios = fields.Float(string="Meta Puntos", compute="_compute_metas", store=False)

    gestion_total = fields.Float(string="% Gestión Total", compute="_compute_gestion_total", store=False)

    @api.depends('fecha')
    def _compute_metas(self):
        for record in self:
            meta = self.env['productividad.configuracion_meta'].search([('proceso', '=', 'almacenamiento')], limit=1, order='id desc')
            if meta:
                record.meta_items_diarios = meta.meta_items_diarios
                record.meta_documentos_diarios = meta.meta_documentos_diarios
                record.meta_puntos_diarios = meta.meta_puntos_diarios
            else:
                record.meta_items_diarios = 0
                record.meta_documentos_diarios = 0
                record.meta_puntos_diarios = 0

    @api.depends('items', 'documentos', 'puntos')
    def _compute_cumplimientos(self):
        meta = self.env['productividad.configuracion_meta'].search([('proceso', '=', 'almacenamiento')], limit=1, order='id desc')
        for record in self:
            if meta:
                record.cumplimiento_items = (record.items / meta.meta_items_diarios) * 100 if meta.meta_items_diarios else 0
                record.cumplimiento_documentos = (record.documentos / meta.meta_documentos_diarios) * 100 if meta.meta_documentos_diarios else 0
                record.cumplimiento_puntos = (record.puntos / meta.meta_puntos_diarios) * 100 if meta.meta_puntos_diarios else 0
            else:
                record.cumplimiento_items = 0
                record.cumplimiento_documentos = 0
                record.cumplimiento_puntos = 0

    @api.depends('items', 'documentos', 'puntos')
    def _compute_gestion_total(self):
        meta = self.env['productividad.configuracion_meta'].search([('proceso', '=', 'almacenamiento')], limit=1, order='id desc')
        for record in self:
            if meta:
                record.gestion_total = round(
                    ((record.documentos / meta.meta_documentos_diarios) * meta.porcentaje_documentos if meta.meta_documentos_diarios else 0) +
                    ((record.items / meta.meta_items_diarios) * meta.porcentaje_items if meta.meta_items_diarios else 0) +
                    ((record.puntos / meta.meta_puntos_diarios) * meta.porcentaje_puntos if meta.meta_puntos_diarios else 0),
                    2
                )
            else:
                record.gestion_total = 0.0
