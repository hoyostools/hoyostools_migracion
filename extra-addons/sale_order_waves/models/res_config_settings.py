from odoo import fields, models, api, _

class RestrictionsConfig(models.TransientModel):
    _inherit = "res.config.settings"

    mostrar_semiautomatico = fields.Selection(related='company_id.mostrar_semiautomatico', readonly=False, selection=[('si','SI'),('no','NO')])
    controlar_desface = fields.Selection(related='company_id.controlar_desface', readonly=False, selection=[('si','SI'),('no','NO')])