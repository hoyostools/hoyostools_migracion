from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = "account.payment"

    tipo_anticipo_id = fields.Many2one(
        comodel_name="ap.anticipo",
        string="Tipo de anticipo"
    )

    anticipo = fields.Boolean(
        string="Anticipo"
    )

    voucher_type = fields.Selection([
        ('pago', 'Pago'),
        ('anticipo', 'Anticipo')
    ], string='Tipo de Pago')

    destination_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Cuenta destino',
        domain="[('account_type', 'in', ['asset_receivable', 'liability_payable'])]"
    )

    @api.onchange('voucher_type')
    def _onchange_voucher_type(self):
        """
        Si cambia a pago limpiamos el tipo de anticipo
        y la cuenta destino.
        """
        if self.voucher_type != 'anticipo':
            self.tipo_anticipo_id = False
            self.destination_account_id = False

    @api.onchange('tipo_anticipo_id')
    def _onchange_tipo_anticipo_id(self):
        """
        Toma la cuenta del tipo de anticipo
        y la coloca automáticamente en destination_account_id
        """
        if self.tipo_anticipo_id:
            self.destination_account_id = self.tipo_anticipo_id.cuenta_anticipo_id.id
            self._origin.destination_account_id = self.tipo_anticipo_id.cuenta_anticipo_id.id

    @api.model
    def _get_destination_account_id(self):
        self.ensure_one()

        if self.voucher_type == 'anticipo' and self.tipo_anticipo_id.cuenta_anticipo_id:
            return self.tipo_anticipo_id.cuenta_anticipo_id

        return super()._get_destination_account_id()

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=False):
        res = super()._prepare_move_line_default_vals(
            write_off_line_vals,
            force_balance=force_balance
        )

        if self.voucher_type == 'anticipo' and self.destination_account_id:
            for line in res:
                if (
                    line.get('account_id')
                    and self.env['account.account'].browse(
                        line['account_id']
                    ).account_type in ['asset_receivable', 'liability_payable']
                ):
                    line['account_id'] = self.destination_account_id.id

        return res