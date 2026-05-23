from odoo import fields, models
from odoo.exceptions import UserError


class SelectSuppliersWizard(models.TransientModel):
    _name = 'semi.auto.reconciliation.supplier.wizard'
    _description = 'Seleccionar rango de vencimiento para proveedores'

    date_due_from = fields.Date(string='Fecha vencimiento desde', required=True)
    date_due_to = fields.Date(string='Fecha vencimiento hasta', required=True)

    def confirm(self):
        if self.date_due_from > self.date_due_to:
            raise UserError(
                'La fecha inicial no puede ser mayor que la fecha final.'
            )

        line_model = self.env[
            'semi.auto.reconciliation.supplier.line'
        ]

        line_model.load_documents_for_due_range(
            self.date_due_from,
            self.date_due_to
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Cruce Proveedores',
            'res_model': 'semi.auto.reconciliation.supplier.line',
            'view_mode': 'tree',
            'target': 'current',
        }