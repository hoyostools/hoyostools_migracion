from odoo import models, fields, api
from odoo.exceptions import UserError

class CarteraClienteWizard(models.TransientModel):
    _name = 'cartera.cliente.wizard'
    _description = 'Wizard para reporte de cartera del cliente'

    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        domain="[('type', '=', 'contact'), ('customer_rank', '>', 0)]"  # <- solo contactos principales
    )

    opcion_reporte = fields.Selection([
        ('todo', 'Todo'),
        ('fecha_vencimiento', 'Fecha de Vencimiento'),
        ('solo_saldo_favor', 'Solo Saldo a Favor'),
    ], string="Opción de Reporte", required=True, default='todo')

    fecha_vencimiento = fields.Date(string="Hasta Fecha de Vencimiento")

    @api.onchange('partner_id')
    def _onchange_partner_domain(self):
        user = self.env.user
        domain = [('type', '=', 'contact'), ('customer_rank', '>', 0)]  # solo contactos principales
        if user.has_group('cartera_cliente.group_cartera_mis_clientes') and \
           not user.has_group('cartera_cliente.group_cartera_clientes_full'):
            domain.append(('user_id', '=', user.id))  # solo clientes asignados
        return {'domain': {'partner_id': domain}}

    def generar_reporte(self):
        self.ensure_one()
        user = self.env.user

        if user.has_group('cartera_cliente.group_cartera_mis_clientes') and \
           not user.has_group('cartera_cliente.group_cartera_clientes_full'):
            if self.partner_id.user_id != user:
                raise UserError(f"No puedes generar reporte de este cliente: {self.partner_id.name}")

        report_ref = self.env.ref('cartera_cliente.action_reporte_cartera_pdf', raise_if_not_found=True)
        return report_ref.report_action(self, data={
            'partner_id': self.partner_id.id,
            'opcion_reporte': self.opcion_reporte,
            'fecha_vencimiento': self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else False
        })
