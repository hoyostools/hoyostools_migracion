from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    def create_dict_invoicehead_dian(self, totales):
        datos = super(AccountMove, self).create_dict_invoicehead_dian(totales)
        for order in self.line_ids.sale_line_ids.order_id:
            if order.b4b and order.servicio_logistico:
                datos['InvoiceComment8'] = 'ambas'
            if order.b4b and not order.servicio_logistico:
                datos['InvoiceComment8'] = 'b4b'
            if not order.b4b and order.servicio_logistico:
                datos['InvoiceComment8'] = 'servicio_logistico'
            if not order.b4b and not order.servicio_logistico:
                datos['InvoiceComment8'] = ''
            if order.notas_logisticas:
                datos['InvoiceComment9'] = order.notas_logisticas
        return datos

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    sale_origin_id = fields.Many2one("sale.order")

    def get_invoice_line_dict(self, index):
        line_dict = super(AccountMoveLine, self).get_invoice_line_dict(index)
        if self.sale_origin_id:
            line_dict['LineComment3'] = self.sale_origin_id.name
        return line_dict