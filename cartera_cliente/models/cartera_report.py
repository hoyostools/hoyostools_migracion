from odoo import models
from datetime import date, datetime

class ReportCarteraCliente(models.AbstractModel):
    _name = 'report.cartera_cliente.reporte_cartera_pdf'
    _description = 'Reporte PDF Cartera Cliente'

    def _get_report_values(self, docids, data=None):
        partner = self.env['res.partner'].browse(data['partner_id'])
        today = date.today()
        opcion_reporte = data.get('opcion_reporte')
        fecha_vencimiento_str = data.get('fecha_vencimiento')
        fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date() if fecha_vencimiento_str else None

        all_partners = partner.child_ids.ids + [partner.id]

        def calcular_dias_vencido(due_date):
            if not due_date:
                return 0, 'black'
            diferencia = (today - due_date).days
            if diferencia > 0:
                return diferencia, 'red'
            else:
                return abs(diferencia), 'green'

        # FACTURAS
        facturas = []
        if opcion_reporte in ['todo', 'fecha_vencimiento']:
            domain = [
                ('partner_id', 'in', all_partners),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'not in', ['paid', 'reversed']),
            ]
            if opcion_reporte == 'fecha_vencimiento' and fecha_vencimiento:
                domain += [
                    ('invoice_date_due', '!=', False),
                    ('invoice_date_due', '<=', fecha_vencimiento),
                ]

            facturas = self.env['account.move'].search(domain)

        # NOTAS DE CRÉDITO
        notas_credito = self.env['account.move'].search([
            ('partner_id', 'in', all_partners),
            ('move_type', '=', 'out_refund'),
            ('state', '=', 'posted'),
            ('payment_state', 'not in', ['paid', 'reversed']),
        ])

        # PAGOS
        payments = self.env['account.payment'].search([
            ('partner_id', 'in', all_partners),
            ('state', '=', 'posted'),
        ])

        pagos_con_saldo = []
        for pay in payments:
            receivable_line = pay.move_id.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
            )
            if receivable_line:
                pagos_con_saldo.append({
                    'name': pay.name,
                    'date': pay.date,
                    'amount_residual': receivable_line[0].amount_residual,
                    'currency': pay.currency_id,
                })

        return {
            'doc_ids': [partner.id],
            'doc_model': 'res.partner',
            'partner': partner,
            'report_date': today,
            'opcion_reporte': opcion_reporte,
            'facturas': sorted([{
                'name': inv.name,
                'invoice_date': inv.invoice_date,
                'due_date': inv.invoice_date_due,
                'dias_vencido': calcular_dias_vencido(inv.invoice_date_due)[0],
                'color': calcular_dias_vencido(inv.invoice_date_due)[1],
                'amount_residual': inv.amount_residual,
                'currency': inv.currency_id,
            } for inv in facturas], key=lambda x: x['due_date'] or date.min),
            'notas_credito': [{
                'name': nc.name,
                'invoice_date': nc.invoice_date,
                'due_date': nc.invoice_date_due,
                'dias_vencido': calcular_dias_vencido(nc.invoice_date_due)[0],
                'color': calcular_dias_vencido(nc.invoice_date_due)[1],
                'amount_residual': nc.amount_residual,
                'currency': nc.currency_id,
            } for nc in notas_credito],
            'payments': pagos_con_saldo,
        }
