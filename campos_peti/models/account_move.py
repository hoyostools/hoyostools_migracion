from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import os
from datetime import datetime
import base64


class AccountMove(models.Model):
    _inherit = 'account.move'

    selected_for_payment = fields.Boolean()
    fecha_bl = fields.Date()
    fecha_vencimiento_FW = fields.Date()
    tasa_FW = fields.Date()
    invoice_status_dian = fields.Selection([])
    documento_equivalente = fields.Char()
    resolution_info = fields.Char()
    resolution_info_per_number = fields.Char()
    loan_line_id = fields.Integer()
    payment_id_anticipo = fields.Integer()
    picking_ids = fields.Integer()
    delivery_count = fields.Integer()
    estado_acuse = fields.Integer()
    estado_rechazo = fields.Integer()
    state_acuse = fields.Integer()
    description_status_dian_acuse = fields.Char()
    dias_recibo = fields.Char()
    doc_period = fields.Integer()
    fecha_recibo = fields.Date()
    period_startdate = fields.Date()