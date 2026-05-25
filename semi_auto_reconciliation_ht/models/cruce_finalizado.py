from odoo import models, fields, api


class CruceSaldos(models.Model):
    _name = 'cruce.saldos'
    _description = 'Cruces Finalizados'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    # -----------------------------
    # Encabezado del cruce
    # -----------------------------
    name = fields.Char(string='Referencia', readonly=True, copy=False, default='Nuevo')
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
        required=True,
        readonly=True
    )
    date = fields.Date(string='Fecha del Cruce', default=fields.Date.today)
    total_amount = fields.Monetary(string='Total Cruzado')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # Asiento soporte del cruce (account.move)
    move_id = fields.Many2one('account.move', string='Asiento Contable Generado')

    # Documentos usados (facturas / NC / pagos)
    line_ids = fields.One2many('cruce.saldos.line', 'cruce_id', string='Documentos Cruzados')

    # Pestaña "Apuntes Contables" (líneas espejo del move_id.line_ids)
    move_line_ids = fields.One2many('cruce.saldos.move.line', 'cruce_id', string='Apuntes Contables')

    # -----------------------------
    # Secuencia + sincronización de apuntes
    # -----------------------------
    @api.model_create_multi
    def create(self, vals_list):
        # 1) Asignar consecutivo si viene "Nuevo"
        # for vals in vals_list:
        #     if vals.get('name', 'Nuevo') == 'Nuevo':
        #         vals['name'] = self.env['ir.sequence'].next_by_code('cruce.saldos') or 'CRUCE'

        # 2) Crear registro(s)
        records = super().create(vals_list)

        # 3) Si ya viene move_id, llenar pestaña "Apuntes Contables"
        records._sync_move_lines_from_move()
        return records

    def write(self, vals):
        # 1) Guardar cambios
        res = super().write(vals)

        # 2) Si cambió move_id, refrescar pestaña "Apuntes Contables"
        if 'move_id' in vals:
            self._sync_move_lines_from_move()
        return res

    def _sync_move_lines_from_move(self):
        """
        Copia EXACTAMENTE las líneas del asiento (move_id.line_ids) hacia
        cruce.saldos.move.line para que se vean en la pestaña "Apuntes Contables".

        - Primero borra las líneas existentes para evitar duplicados
        - Luego crea una línea por cada account.move.line del asiento
        """
        for cruce in self:
            if not cruce.move_id:
                continue

            # Evitar duplicados: borramos y recreamos
            cruce.move_line_ids.unlink()

            vals_list = []
            for aml in cruce.move_id.line_ids:
                vals_list.append({
                    'cruce_id': cruce.id,
                    'move_line_id': aml.id,
                })

            if vals_list:
                self.env['cruce.saldos.move.line'].create(vals_list)

    # -----------------------------
    # Botón para abrir el asiento
    # -----------------------------
    def action_open_account_move(self):
        self.ensure_one()
        if not self.move_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asiento Contable',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.move_id.id,
            'target': 'current',
        }


class CruceSaldosLine(models.Model):
    _name = 'cruce.saldos.line'
    _description = 'Documentos Cruzados'

    cruce_id = fields.Many2one('cruce.saldos', string='Cruce', ondelete='cascade')
    move_id = fields.Many2one('account.move', string='Documento')
    payment_id = fields.Many2one('account.payment', string='Pago')
    document_type = fields.Selection([
        ('invoice', 'Factura'),
        ('credit_note', 'Nota de Crédito'),
        ('payment', 'Pago')
    ], string='Tipo Documento')
    amount_applied = fields.Monetary(string='Importe Aplicado')
    currency_id = fields.Many2one('res.currency', related='cruce_id.currency_id', readonly=True)

    invoice_number = fields.Char(string='Factura', compute='_compute_document_numbers', store=False)
    credit_note_number = fields.Char(string='Nota de Crédito', compute='_compute_document_numbers', store=False)
    payment_number = fields.Char(string='Pago', compute='_compute_document_numbers', store=False)

    @api.depends('document_type', 'move_id.name', 'payment_id.name')
    def _compute_document_numbers(self):
        for line in self:
            line.invoice_number = line.move_id.name if line.document_type == 'invoice' else ''
            line.credit_note_number = line.move_id.name if line.document_type == 'credit_note' else ''
            line.payment_number = line.payment_id.name if line.document_type == 'payment' else ''


class CruceSaldosMoveLine(models.Model):
    _name = 'cruce.saldos.move.line'
    _description = 'Apuntes Contables del Cruce'

    cruce_id = fields.Many2one('cruce.saldos', string='Cruce', ondelete='cascade')

    # Referencia real al apunte contable del asiento
    move_line_id = fields.Many2one('account.move.line', string='Apunte Contable', required=True)

    # Cuenta tomada del apunte (solo lectura)
    account_id = fields.Many2one(related='move_line_id.account_id', string='Cuenta', readonly=True)

    # Moneda (la del cruce)
    currency_id = fields.Many2one('res.currency', related='cruce_id.currency_id', readonly=True)

    # Importe calculado desde el apunte: debit - credit (balance)
    amount = fields.Monetary(
        string='Importe',
        currency_field='currency_id',
        compute='_compute_amount',
        store=True,
        readonly=True
    )

    @api.depends('move_line_id.debit', 'move_line_id.credit')
    def _compute_amount(self):
        for rec in self:
            rec.amount = (rec.move_line_id.debit or 0.0) - (rec.move_line_id.credit or 0.0)