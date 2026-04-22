from odoo import fields, models


class GeneralExogenus(models.Model):
    _name = 'general.exogenus'
    _description = 'General de Información Exógena'

    total_account = fields.Selection(
        selection=[
            ('debit', 'Débito'),
            ('credit', 'Crédito'),
            ('deb_cre', 'Débito-Crédito'),
            ('cre_deb', 'Crédito-Débito'),
            ('total', 'Saldo')
        ],
        string='Tipo de Valor'
    )

    concept_id = fields.Many2one(
        comodel_name='concept.exogenus',
        string='Concepto'
    )

    format_account_id = fields.Many2one(
        comodel_name='account.exogenus',
        string='Cuenta'
    )

    column_id = fields.Many2one(
        comodel_name='column.exogenus',
        string='Categoría'
    )

    format_id = fields.Many2one(
        comodel_name='format.exogenus',
        string='Formato'
    )

    exogena_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Diarios Exógena'
    )

    code_general = fields.Integer(
        string='Código',
        related='format_id.code_format',
        store=True
    )
