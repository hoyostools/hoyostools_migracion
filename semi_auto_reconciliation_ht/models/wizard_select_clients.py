from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class SelectClientsWizard(models.TransientModel):
    _name = 'semi.auto.reconciliation.client.wizard'
    _description = 'Seleccionar Clientes para Conciliación'

    user_id = fields.Many2one(
        'res.users',
        string='Vendedor',
        domain="[('share', '=', False)]"
    )
    partner_ids = fields.Many2many(
        'res.partner',
        string="Clientes",
        domain="[('id', 'in', available_partner_ids)]"
    )
    available_partner_ids = fields.Many2many(
        'res.partner',
        compute='_compute_available_partner_ids',
    )

    @api.depends('user_id')
    def _compute_available_partner_ids(self):
        for wizard in self:
            wizard.available_partner_ids = [(5, 0, 0)]

            # 1. Obtener todos los partners (padres e hijos) que tengan documentos y coincidan con el vendedor
            if wizard.user_id:
                # Contactos principales del vendedor
                parent_partners = self.env['res.partner'].search([
                    ('user_id', '=', wizard.user_id.id),
                    ('parent_id', '=', False)
                ])

                # Incluir sus hijos (direcciones, etc.)
                child_partners = self.env['res.partner'].search([
                    ('parent_id', 'in', parent_partners.ids)
                ])

                all_partner_ids = parent_partners.ids + child_partners.ids
            else:
                # Si no se seleccionó vendedor, usar todos los contactos principales y sus hijos
                parent_partners = self.env['res.partner'].search([('parent_id', '=', False)])
                child_partners = self.env['res.partner'].search([('parent_id', 'in', parent_partners.ids)])
                all_partner_ids = parent_partners.ids + child_partners.ids

            # Buscar documentos de esos partners
            invoices = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', '!=', 'paid'),
                ('amount_residual', '>', 0),
                ('partner_id', 'in', all_partner_ids),
            ])

            credit_notes = self.env['account.move'].search([
                ('move_type', '=', 'out_refund'),
                ('state', '=', 'posted'),
                ('payment_state', '!=', 'paid'),
                ('amount_residual', '>', 0),
                ('partner_id', 'in', all_partner_ids),
            ])

            payments = self.env['account.payment'].search([
                ('state', '=', 'posted'),
                ('partner_id', 'in', all_partner_ids),
                ('move_id.line_ids.account_id.account_type', '=', 'asset_receivable'),
                ('move_id.line_ids.reconciled', '=', False),
            ])

            # Determinar qué partners tienen facturas + (pagos o NC)
            invoice_partners = set(invoices.mapped('partner_id.commercial_partner_id.id'))
            credit_note_partners = set(credit_notes.mapped('partner_id.commercial_partner_id.id'))
            payment_partners = set(payments.mapped('partner_id.commercial_partner_id.id'))

            valid_partners = invoice_partners & (credit_note_partners | payment_partners)

            wizard.available_partner_ids = [(6, 0, list(valid_partners))]

    def confirm(self):
        if not self.partner_ids:
            return

        self.env['semi.auto.reconciliation.line'].search([]).unlink()
        self.env['semi.auto.reconciliation.line'].load_documents_for_partners(self.partner_ids)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Conciliación Semiautomática',
            'res_model': 'semi.auto.reconciliation.line',
            'view_mode': 'tree',
            'target': 'current',
            'domain': [('partner_id', 'in', self.partner_ids.ids)],
        }