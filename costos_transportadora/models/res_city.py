from odoo import models, fields


class ResCity(models.Model):
    _inherit = 'res.city'
    
    ciudad_principal = fields.Boolean(
        string='¿Ciudad Principal?'
    )

    transportadora_id = fields.Many2one(
        'transportadora.transportadora',
        string='Transportadora'
    )

    valor_caja = fields.Float(
        string='Valor Caja',
        digits=(16, 2)
    )

    code = fields.Char(
        string='Código Ciudad'
    )