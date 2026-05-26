from odoo import models, fields, api


class CruceSaldosSupplier(models.Model):
    _name = 'cruce.saldos.supplier'
    _description = 'Cruces Finalizados Proveedores'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(string='Referencia', readonly=True, copy=False, default='Nuevo')
    partner_id = fields.Many2one('res.partner', string='Proveedor', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True, readonly=True)
    date = fields.Date(string='Fecha del Cruce', default=fields.Date.today)
    total_amount = fields.Monetary(string='Total Cruzado')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    move_id = fields.Many2one('account.move', string='Asiento Contable Generado')
    line_ids = fields.One2many('cruce.saldos.supplier.line', 'cruce_id', string='Documentos Cruzados')
    move_line_ids = fields.One2many('cruce.saldos.supplier.move.line', 'cruce_id', string='Apuntes Contables')

    @api.model_create_multi
    def create(self, vals_list):
        # for vals in vals_list:
        #     if vals.get('name', 'Nuevo') == 'Nuevo':
        #         vals['name'] = (
        #             self.env['ir.sequence'].next_by_code(
        #                 'cruce.saldos.supplier'
        #             ) or 'CRUP'
        #         )

        records = super().create(vals_list)
        records._sync_move_lines_from_move()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'move_id' in vals:
            self._sync_move_lines_from_move()
        return res

    def _sync_move_lines_from_move(self):
        for cruce in self:
            if not cruce.move_id:
                continue

            cruce.move_line_ids.unlink()

            vals_list = []
            for aml in cruce.move_id.line_ids:
                vals_list.append({
                    'cruce_id': cruce.id,
                    'move_line_id': aml.id,
                })

            if vals_list:
                self.env[
                    'cruce.saldos.supplier.move.line'
                ].create(vals_list)

    def action_open_account_move(self):
        self.ensure_one()

        if not self.move_id:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': 'Asiento Contable',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.move_id.id,
            'target': 'current',
        }


class CruceSaldosSupplierLine(models.Model):
    _name = 'cruce.saldos.supplier.line'
    _description = 'Documentos Cruzados Proveedores'

    cruce_id = fields.Many2one('cruce.saldos.supplier', string='Cruce', ondelete='cascade')
    move_id = fields.Many2one('account.move', string='Documento')
    payment_id = fields.Many2one('account.payment', string='Pago')
    document_type = fields.Selection([('invoice', 'Factura'),('credit_note', 'Nota de Crédito'),('payment', 'Pago'),], string='Tipo Documento')
    amount_applied = fields.Monetary(string='Importe Aplicado')
    currency_id = fields.Many2one('res.currency', related='cruce_id.currency_id', readonly=True)
    invoice_number = fields.Char(string='Factura', compute='_compute_document_numbers')
    credit_note_number = fields.Char(string='Nota de Crédito', compute='_compute_document_numbers')
    payment_number = fields.Char(string='Pago', compute='_compute_document_numbers')

    @api.depends('document_type', 'move_id.name', 'payment_id.name')
    def _compute_document_numbers(self):
        for line in self:
            line.invoice_number = (
                line.move_id.name
                if line.document_type == 'invoice'
                else ''
            )
            line.credit_note_number = (
                line.move_id.name
                if line.document_type == 'credit_note'
                else ''
            )
            line.payment_number = (
                line.payment_id.name
                if line.document_type == 'payment'
                else ''
            )


class CruceSaldosSupplierMoveLine(models.Model):
    _name = 'cruce.saldos.supplier.move.line'
    _description = 'Apuntes Contables del Cruce Proveedores'

    cruce_id = fields.Many2one('cruce.saldos.supplier', string='Cruce', ondelete='cascade')
    move_line_id = fields.Many2one('account.move.line', string='Apunte Contable', required=True)
    account_id = fields.Many2one(related='move_line_id.account_id', string='Cuenta', readonly=True)
    currency_id = fields.Many2one('res.currency', related='cruce_id.currency_id', readonly=True)
    amount = fields.Monetary(string='Importe', currency_field='currency_id', compute='_compute_amount', store=True, readonly=True)

    @api.depends('move_line_id.debit', 'move_line_id.credit')
    def _compute_amount(self):
        for rec in self:
            rec.amount = (
                rec.move_line_id.debit or 0.0
            ) - (
                rec.move_line_id.credit or 0.0
            )