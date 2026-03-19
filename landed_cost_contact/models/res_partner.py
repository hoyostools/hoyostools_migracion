from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    lc_flete_internacional = fields.Boolean("FLETE INTERNACIONAL")
    lc_flete_nacional = fields.Boolean("FLETE NACIONAL")
    lc_mov_log_tinkano = fields.Boolean("MOVIMIENTOS LOGISTICOS (TINKANO)")
    lc_mov_log_yalusa = fields.Boolean("MOVIMIENTOS LOGISTICOS (YALUSA)")
    lc_cuadrilla_descargue = fields.Boolean("CUADRILLA DESCARGUE")
    lc_agenciamiento_aduanero = fields.Boolean("AGENCIAMIENTO ADUANERO")
    lc_satelital = fields.Boolean("SATELITAL")
    lc_planilla_traslado = fields.Boolean("PLANILLA DE TRASLADO")
    lc_zona_franca = fields.Boolean("ZONA FRANCA")
    lc_registro_impo = fields.Boolean("REGISTRO IMPO")
    lc_gastos_origen = fields.Boolean("GASTOS EN ORIGEN")