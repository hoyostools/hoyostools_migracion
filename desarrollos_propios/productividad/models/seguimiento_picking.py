from odoo import models, fields, api


class SeguimientoPicking(models.Model):
    _name = 'productividad.seguimiento_picking'
    _description = 'Seguimiento Diario de Pickers'
    _order = 'fecha desc'

    user_id = fields.Many2one('res.users', string="Nombre del Picker", required=True)

    fecha = fields.Date(string="Fecha", required=True)

    turno_id = fields.Many2one(
        'productividad.turno',
        string="Turno",
        required=True
    )

    items = fields.Integer(string="Items", default=0)
    documentos = fields.Integer(string="Documentos", default=0)
    puntos = fields.Float(string="Puntos", default=0.0)

    configuracion_id = fields.Many2one(
        'productividad.tablero_configuracion',
        compute='_compute_configuracion',
        store=True,
        string='Configuración del Usuario'
    )

    @api.depends('user_id')
    def _compute_configuracion(self):
        for rec in self:
            config = self.env['productividad.tablero_configuracion'].search([
                ('user_id', '=', rec.user_id.id),
                ('funcion', '=', 'separador')
            ], limit=1)
            rec.configuracion_id = config

    # ==========================
    # METAS
    # ==========================

    meta_items_diarios = fields.Integer(compute="_compute_metas")
    meta_documentos_diarios = fields.Integer(compute="_compute_metas")
    meta_puntos_diarios = fields.Float(compute="_compute_metas")

    cumplimiento_items = fields.Float(compute="_compute_cumplimientos", store=True)
    cumplimiento_documentos = fields.Float(compute="_compute_cumplimientos", store=True)
    cumplimiento_puntos = fields.Float(compute="_compute_cumplimientos", store=True)

    gestion_total = fields.Float(string="% Gestión Total", compute="_compute_gestion_total", store=True)

    def _get_meta(self, user):
        configuracion = self.env['productividad.tablero_configuracion'].search([
            ('user_id', '=', user.id)
        ], limit=1)

        if configuracion and configuracion.combo_pasillo_id:
            combo = configuracion.combo_pasillo_id
            return {
                'items': combo.items,
                'documentos': combo.documentos,
                'puntos': combo.puntos,
                'porcentaje_items': 1/3,
                'porcentaje_documentos': 1/3,
                'porcentaje_puntos': 1/3
            }

        meta_general = self.env['productividad.configuracion_meta'].search(
            [('proceso', '=', 'picking')],
            limit=1,
            order='id desc'
        )

        if meta_general:
            return {
                'items': meta_general.meta_items_diarios,
                'documentos': meta_general.meta_documentos_diarios,
                'puntos': meta_general.meta_puntos_diarios,
                'porcentaje_items': meta_general.porcentaje_items,
                'porcentaje_documentos': meta_general.porcentaje_documentos,
                'porcentaje_puntos': meta_general.porcentaje_puntos
            }

        return {
            'items': 0,
            'documentos': 0,
            'puntos': 0,
            'porcentaje_items': 0,
            'porcentaje_documentos': 0,
            'porcentaje_puntos': 0
        }

    @api.depends('user_id')
    def _compute_metas(self):
        for record in self:
            meta = record._get_meta(record.user_id)
            record.meta_items_diarios = meta['items']
            record.meta_documentos_diarios = meta['documentos']
            record.meta_puntos_diarios = meta['puntos']

    @api.depends('items', 'documentos', 'puntos', 'user_id')
    def _compute_cumplimientos(self):
        for record in self:
            meta = record._get_meta(record.user_id)

            record.cumplimiento_items = (
                (record.items / meta['items']) * 100 if meta['items'] else 0
            )
            record.cumplimiento_documentos = (
                (record.documentos / meta['documentos']) * 100 if meta['documentos'] else 0
            )
            record.cumplimiento_puntos = (
                (record.puntos / meta['puntos']) * 100 if meta['puntos'] else 0
            )

    @api.depends('items', 'documentos', 'puntos', 'user_id')
    def _compute_gestion_total(self):
        for record in self:
            meta = record._get_meta(record.user_id)

            total = 0
            if meta['documentos']:
                total += (record.documentos / meta['documentos']) * meta['porcentaje_documentos']
            if meta['items']:
                total += (record.items / meta['items']) * meta['porcentaje_items']
            if meta['puntos']:
                total += (record.puntos / meta['puntos']) * meta['porcentaje_puntos']

            record.gestion_total = round(total * 100, 2)
            
    
