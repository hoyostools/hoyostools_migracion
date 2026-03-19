from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    presupuesto_transportadora_regional = fields.Float(
        string='Presupuesto Transportadora Regional (%)',
        config_parameter='costos_transportadora.presupuesto_transportadora_regional'
    )

    presupuesto_transportadora_principal = fields.Float(
        string='Presupuesto Transportadora Principal (%)',
        config_parameter='costos_transportadora.presupuesto_transportadora_principal'
    )
