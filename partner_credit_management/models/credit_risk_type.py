# -*- coding: utf-8 -*-
from odoo import fields, models


class CreditRiskType(models.Model):
    _name = "credit.risk.type"
    _description = "Tipo de Riesgo de Crédito"
    _order = "name"

    name = fields.Char(string="Nombre", required=True)
    days_overdue = fields.Integer(string="Días Mora", required=True, default=0)
    active = fields.Boolean(string="Activo", default=True)