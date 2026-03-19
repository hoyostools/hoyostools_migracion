from odoo import models, fields, api
from datetime import timedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

    def create_dict_invoicehead_dian(self, totales):
        datos = super(AccountMove, self).create_dict_invoicehead_dian(totales)
        subtotal_descuento = round(self.amount_untaxed * (self.invoice_payment_term_id.discount_percentage / 100), 2)
        total_descuento = self.amount_total_in_currency_signed - subtotal_descuento
        fecha_pago_anticipado = self.invoice_date + timedelta(days=self.invoice_payment_term_id.discount_days)
        fecha_pago_anticipado_str = fecha_pago_anticipado.strftime('%d/%m/%Y')
        total_descuento_formateado = f"${total_descuento:,.2f}"
        datos['InvoiceComment7'] = f"{total_descuento_formateado} si paga antes de {fecha_pago_anticipado_str}"
        return datos
