from odoo import models, fields, api


class StockLandedCostLine(models.Model):
    _inherit = "stock.landed.cost.lines"

    contact_id = fields.Many2one(
        "res.partner",
        string="Contacto",
    )

    allowed_contact_ids = fields.Many2many(
        "res.partner",
        string="Allowed Contacts",
        compute="_compute_allowed_contact_ids",
    )

    @api.depends("name")
    def _compute_allowed_contact_ids(self):
        Partner = self.env["res.partner"]

        for line in self:
            partners = Partner.browse()

            name = (line.name or "").upper().strip()

            if "FLETE INTERNACIONAL" in name:
                partners = Partner.search([("lc_flete_internacional", "=", True)])

            elif "FLETE NACIONAL" in name:
                partners = Partner.search([("lc_flete_nacional", "=", True)])

            elif "MOVIMIENTOS LOGISTICOS(TINKANO)" in name or "MOVIMIENTOS LOGISTICOS (TINKANO)" in name or "TINKANO" in name:
                partners = Partner.search([("lc_mov_log_tinkano", "=", True)])

            elif "MOVIMIENTOS LOGISTICOS(YALUSA)" in name or "MOVIMIENTOS LOGISTICOS (YALUSA)" in name or "YALUSA" in name:
                partners = Partner.search([("lc_mov_log_yalusa", "=", True)])

            elif "CUADRILLA DESCARGUE" in name:
                partners = Partner.search([("lc_cuadrilla_descargue", "=", True)])

            elif "AGENCIAMIENTO ADUANERO" in name:
                partners = Partner.search([("lc_agenciamiento_aduanero", "=", True)])

            elif "SATELITAL" in name:
                partners = Partner.search([("lc_satelital", "=", True)])

            elif "PLANILLA DE TRASLADO" in name:
                partners = Partner.search([("lc_planilla_traslado", "=", True)])

            elif "ZONA FRANCA" in name:
                partners = Partner.search([("lc_zona_franca", "=", True)])

            elif "REGISTRO IMPO" in name:
                partners = Partner.search([("lc_registro_impo", "=", True)])

            elif "GASTOS EN ORIGEN" in name:
                partners = Partner.search([("lc_gastos_origen", "=", True)])

            line.allowed_contact_ids = partners

            if line.contact_id and line.contact_id not in partners:
                line.contact_id = False