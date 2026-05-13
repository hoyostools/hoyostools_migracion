from odoo import models, fields, api

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    voucher_type = fields.Selection([
        ('pago', 'Pago'),
        ('anticipo', 'Anticipo')
    ], string='Tipo de Pago')

    destination_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Cuenta destino',
        domain="[('account_type', 'in', ['asset_receivable', 'liability_payable'])]"
    )
    
    @api.model
    def _get_destination_account_id(self):
        return self.destination_account_id.id if self.destination_account_id else super()._get_destination_account_id()

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=False):
        res = super()._prepare_move_line_default_vals(write_off_line_vals, force_balance=force_balance)
        if self.voucher_type == 'anticipo' and self.destination_account_id:
            for line in res:
                # Identificamos la línea donde va la cuenta del cliente (receivable/payable)
                if line.get('account_id') and self.env['account.account'].browse(line['account_id']).account_type in ['asset_receivable', 'liability_payable']:
                    line['account_id'] = self.destination_account_id.id
        return res