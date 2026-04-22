from odoo import fields, models

class ColumnExogenus(models.Model):
    _name = 'column.exogenus'
    _description = 'Column Exogenus'
    _order = 'sequence'

    #  campos creacion columnas
    name = fields.Char(string="Name")
    technical_name = fields.Char(string="Name technical")
    format_exogenus_column_id = fields.Many2one('format.exogenus',string="format")
    sequence = fields.Integer(string='Secuence', default='1')
    account = fields.Boolean(string='Cuentas')
