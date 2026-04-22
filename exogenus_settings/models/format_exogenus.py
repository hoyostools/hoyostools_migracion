from odoo import api, fields, models

class FormatExogenus(models.Model):
    _name = 'format.exogenus'
    _description = 'Formato de Información Exógena'

    name = fields.Char(string="Nombre")
    description_format = fields.Char(string="Descripción")
    
    type_format = fields.Selection(
        selection=[
            ('format_1001', 'FORMATO_1001'),
            ('format_1003', 'FORMATO_1003'),
            ('format_1004', 'FORMATO_1004'),
            ('format_1005', 'FORMATO_1005'),
            ('format_1006', 'FORMATO_1006'),
            ('format_1007', 'FORMATO_1007'),
            ('format_1008', 'FORMATO_1008'),
            ('format_1009', 'FORMATO_1009'),
            ('format_1010', 'FORMATO_1010'),
            ('format_1011', 'FORMATO_1011'),
            ('format_1012', 'FORMATO_1012'),
            ('format_1056', 'FORMATO_1056'),
            ('format_1647', 'FORMATO_1647'),
            ('format_2276', 'FORMATO_2276'),
        ],
        string='Tipo de Formato'
    )

    code_format = fields.Integer(string="Código")

    general_id = fields.One2many(
        comodel_name='general.exogenus',
        inverse_name='format_id',
        string='Generales'
    )

    column_ids = fields.One2many(
        comodel_name='column.exogenus',
        inverse_name='format_exogenus_column_id',
        string='Columnas'
    )

    @api.onchange('type_format')
    def _onchange_type_format(self):
        if self.type_format:
            columns = self.env['column.exogenus'].search([
                ('format_exogenus_column_id.type_format', '=', self.type_format)
            ])
            self.column_ids = [(6, 0, columns.ids)]
