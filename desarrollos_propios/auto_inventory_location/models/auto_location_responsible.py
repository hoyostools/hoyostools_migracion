from odoo import models, fields, api


class AutoLocationResponsible(models.Model):
    _name = "auto.location.responsible"
    _description = "Configuración de responsables de auto ubicación"

    user_id = fields.Many2one(
        "res.users",
        string="Responsable",
        required=True
    )

    picking_count = fields.Integer(
        string="Albaranes asignados"
    )

    origen_bienes = fields.Selection(
        [
            ("nacional", "Nacional"),
            ("importado", "Importado"),
        ],
        string="Origen de bienes"
    )

    @api.depends("user_id")
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = self.env["stock.picking"].search_count([
                ("user_id", "=", rec.user_id.id),
                ("state", "not in", ["done", "cancel"]),
                ("picking_type_code", "=", "internal")
            ])

