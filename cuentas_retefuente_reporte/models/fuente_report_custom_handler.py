# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class FuenteReportCustomHandler(models.AbstractModel):
    _inherit = 'l10n_co.fuente.report.handler'
    _description = 'Fuente Report Custom Handler'

    def _get_domain(self, report, options, line_dict_id=None):
        domain = super()._get_domain(report, options, line_dict_id=line_dict_id)
        domain += [('account_id.visible_reporte_retencion', '=', True)]
        return domain
