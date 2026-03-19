# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    visible_reporte_retencion = fields.Boolean(
        string='Visible en reporte',
        default=False,
        help='Indica si esta cuenta debe mostrarse en el reporte de retención en la fuente.'
    )
