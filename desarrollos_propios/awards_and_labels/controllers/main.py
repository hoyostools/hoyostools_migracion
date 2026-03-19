from odoo import http
from odoo.http import request

class AwardSorteoController(http.Controller):

    @http.route(['/sorteo/resultado/<int:sorteo_id>'], type='http', auth='public', website=True)
    def sorteo_resultado(self, sorteo_id, **kwargs):
        sorteo = request.env['awards_and_labels.award_sorteo'].sudo().browse(sorteo_id)
        if not sorteo.exists():
            return request.not_found()

        return request.render('awards_and_labels.sorteo_result_template', {
            'sorteo': sorteo,
            'award': sorteo.award_id,
            'winner': sorteo.winner_id,
            'tickets': sorteo.winner_tickets,
        })