from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    load_default_origin_pos = fields.Boolean(string="Cargar por defecto en POS Origen")
    load_default_dest_pos = fields.Boolean(string="Cargar por defecto en POS Destino")

    @api.constrains('load_default_origin_pos', 'load_default_dest_pos')
    def _check_load_default_pos(self):
        for record in self:
            # Validar que solo haya un registro con 'load_default_origin_pos' como True
            if record.load_default_origin_pos:
                existing_origin = self.search([
                    ('id', '!=', record.id),
                    ('load_default_origin_pos', '=', True)
                ])
                if existing_origin:
                    raise ValidationError(
                        "Solo puede haber un registro con 'Cargar por defecto en POS Origen' establecido como True."
                    )

            # Validar que solo haya un registro con 'load_default_dest_pos' como True
            if record.load_default_dest_pos:
                existing_dest = self.search([
                    ('id', '!=', record.id),
                    ('load_default_dest_pos', '=', True)
                ])
                if existing_dest:
                    raise ValidationError(
                        "Solo puede haber un registro con 'Cargar por defecto en POS Destino' establecido como True."
                    )


