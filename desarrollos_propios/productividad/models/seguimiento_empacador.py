from odoo import models, fields, api


class SeguimientoEmpacador(models.Model):
    _name = 'productividad.seguimiento_empacador'
    _description = 'Seguimiento Diario de Empacadores'
    _order = 'fecha desc'

    user_id = fields.Many2one('res.users', string="Nombre del Empacador", required=True)
    fecha = fields.Date(string="Fecha", required=True)

    turno_id = fields.Many2one(
        'productividad.turno',
        string="Turno",
        required=True
    )

    items = fields.Integer(default=0)
    documentos = fields.Integer(default=0)
    puntos = fields.Float(default=0.0)

    # 🔥 IMPORTANTE: store=True para que el mensual lo pueda sumar correctamente
    ahorro = fields.Float(string="Ahorro", default=0.0, store=True)

    configuracion_id = fields.Many2one(
        'productividad.tablero_configuracion',
        compute='_compute_configuracion',
        store=True
    )

    # ==========================
    # CAJAS
    # ==========================

    cajas_usadas = fields.Integer(string="C. Usadas", default=0)
    cantidad_maxima_cajas = fields.Integer(string="C. Máx", default=0)

    porcentaje_cajas = fields.Float(
        string="% Eficiencia Cajas",
        compute="_compute_porcentaje_cajas",
        store=True
    )

    @api.depends('cajas_usadas', 'cantidad_maxima_cajas')
    def _compute_porcentaje_cajas(self):
        for record in self:
            if record.cantidad_maxima_cajas > 0:
                record.porcentaje_cajas = (
                    (record.cantidad_maxima_cajas - record.cajas_usadas)
                    / record.cantidad_maxima_cajas
                ) * 100
            else:
                record.porcentaje_cajas = 0

    @api.depends('user_id')
    def _compute_configuracion(self):
        for rec in self:
            config = self.env['productividad.tablero_configuracion'].search([
                ('user_id', '=', rec.user_id.id),
                ('funcion', '=', 'empacador')
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

    gestion_total = fields.Float(compute="_compute_gestion_total", store=True)

    @api.depends('fecha')
    def _compute_metas(self):
        for record in self:
            record.meta_items_diarios = 0
            record.meta_documentos_diarios = 0
            record.meta_puntos_diarios = 0

            if not record.fecha:
                continue

            meta = self.env['productividad.configuracion_meta'].search([
                ('proceso', '=', 'packing'),
                ('fecha_inicio', '<=', record.fecha),
                ('fecha_fin', '>=', record.fecha)
            ], limit=1)

            if meta:
                record.meta_items_diarios = meta.meta_items_diarios
                record.meta_documentos_diarios = meta.meta_documentos_diarios
                record.meta_puntos_diarios = meta.meta_puntos_diarios

    @api.depends('items', 'documentos', 'puntos', 'fecha')
    def _compute_cumplimientos(self):
        for record in self:
            record.cumplimiento_items = 0
            record.cumplimiento_documentos = 0
            record.cumplimiento_puntos = 0

            if not record.fecha:
                continue

            meta = self.env['productividad.configuracion_meta'].search([
                ('proceso', '=', 'packing'),
                ('fecha_inicio', '<=', record.fecha),
                ('fecha_fin', '>=', record.fecha)
            ], limit=1)

            if not meta:
                continue

            if meta.meta_items_diarios:
                record.cumplimiento_items = (
                    record.items / meta.meta_items_diarios
                ) * 100

            if meta.meta_documentos_diarios:
                record.cumplimiento_documentos = (
                    record.documentos / meta.meta_documentos_diarios
                ) * 100

            if meta.meta_puntos_diarios:
                record.cumplimiento_puntos = (
                    record.puntos / meta.meta_puntos_diarios
                ) * 100

    @api.depends('items', 'documentos', 'puntos', 'fecha')
    def _compute_gestion_total(self):
        for record in self:
            record.gestion_total = 0

            if not record.fecha:
                continue

            meta = self.env['productividad.configuracion_meta'].search([
                ('proceso', '=', 'packing'),
                ('fecha_inicio', '<=', record.fecha),
                ('fecha_fin', '>=', record.fecha)
            ], limit=1)

            if not meta:
                continue

            total = 0

            if meta.meta_documentos_diarios:
                total += (
                    (record.documentos / meta.meta_documentos_diarios)
                    * meta.porcentaje_documentos
                )

            if meta.meta_items_diarios:
                total += (
                    (record.items / meta.meta_items_diarios)
                    * meta.porcentaje_items
                )

            if meta.meta_puntos_diarios:
                total += (
                    (record.puntos / meta.meta_puntos_diarios)
                    * meta.porcentaje_puntos
                )

            record.gestion_total = round(total * 100, 2)

    # ==========================
    # ACTUALIZAR RESUMEN MENSUAL
    # ==========================

    def _update_resumen_mensual(self):
        Resumen = self.env['productividad.resumen_empacador_mensual'].sudo()

        for record in self:
            if not record.user_id or not record.fecha:
                continue

            mes = record.fecha.month
            anio = record.fecha.year

            resumen = Resumen.search([
                ('user_id', '=', record.user_id.id),
                ('mes', '=', mes),
                ('anio', '=', anio),
            ], limit=1)

            if not resumen:
                Resumen.create({
                    'user_id': record.user_id.id,
                    'mes': mes,
                    'anio': anio,
                })
            resumen._compute_totales()

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._update_resumen_mensual()
        return record

    def write(self, vals):
        res = super().write(vals)
        self._update_resumen_mensual()
        return res