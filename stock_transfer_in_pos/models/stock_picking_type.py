from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    load_default_pos = fields.Boolean(string="Cargar por defecto en POS")

    @api.constrains('load_default_pos')
    def _check_load_default_pos(self):
        for record in self:
            if record.load_default_pos:
                # Buscar otros registros con load_default_pos=True
                existing = self.search([
                    ('id', '!=', record.id),
                    ('load_default_pos', '=', True)
                ])
                if existing:
                    raise ValidationError(
                        "Solo puede haber un registro con 'Cargar por defecto en POS' establecido como True.")


