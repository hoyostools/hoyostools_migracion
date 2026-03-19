from odoo import fields, models, api, _

class ResCompany(models.Model):
    _inherit = "res.company"

    mostrar_semiautomatico = fields.Selection(default='si', readonly=False, selection=[('si','SI'),('no','NO')])
    controlar_desface = fields.Selection(default='no', readonly=False, selection=[('si','SI'),('no','NO')])