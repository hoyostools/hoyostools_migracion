from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ResumenEmpacadorMensual(models.Model):
    _name = 'productividad.resumen_empacador_mensual'
    _description = 'Resumen Mensual Empacadores'
    _order = 'anio desc, mes desc'

    user_id = fields.Many2one('res.users', string="Empacador", required=True)
    mes = fields.Integer(string="Mes", required=True)
    anio = fields.Integer(string="Año", required=True)

    items = fields.Integer(string="Items", compute="_compute_totales", store=True)
    documentos = fields.Integer(string="Documentos", compute="_compute_totales", store=True)
    puntos = fields.Float(string="Puntos", compute="_compute_totales", store=True)

    cajas_usadas = fields.Integer(string="Cajas Usadas", compute="_compute_totales", store=True)
    cantidad_maxima_cajas = fields.Integer(string="Cajas Máx", compute="_compute_totales", store=True)

    ahorro = fields.Float(string="Ahorro", compute="_compute_totales", store=True)

    # 🔥 IMPORTANTE: agregar depends vacío para forzar recalculo manual
    @api.depends('user_id', 'mes', 'anio')
    def _compute_totales(self):
        Seguimiento = self.env['productividad.seguimiento_empacador']

        for record in self:
            record.items = 0
            record.documentos = 0
            record.puntos = 0
            record.cajas_usadas = 0
            record.cantidad_maxima_cajas = 0
            record.ahorro = 0

            if not record.user_id or not record.mes or not record.anio:
                continue

            fecha_inicio = datetime(record.anio, record.mes, 1)
            fecha_fin = fecha_inicio + relativedelta(months=1)

            seguimientos = Seguimiento.search([
                ('user_id', '=', record.user_id.id),
                ('fecha', '>=', fecha_inicio.date()),
                ('fecha', '<', fecha_fin.date()),
            ])

            record.items = sum(s.items for s in seguimientos)
            record.documentos = sum(s.documentos for s in seguimientos)
            record.puntos = sum(s.puntos for s in seguimientos)
            record.cajas_usadas = sum(s.cajas_usadas for s in seguimientos)
            record.cantidad_maxima_cajas = sum(s.cantidad_maxima_cajas for s in seguimientos)
            record.ahorro = sum(s.ahorro for s in seguimientos)