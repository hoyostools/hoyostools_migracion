from odoo import models, fields, api
from odoo.exceptions import UserError
import random

class AwardSorteo(models.TransientModel):
    _name = 'awards_and_labels.award_sorteo'
    _description = 'Virtual Award Draw'

    award_id = fields.Many2one('awards_and_labels.award', string='Premio', required=True)
    winner_id = fields.Many2one('res.partner', string='Ganador', readonly=True)
    winner_tickets = fields.Integer(string='Tiquetes del Ganador', readonly=True)

    def action_realizar_sorteo(self):
        partner_awards = self.env['awards_and_labels.res_partner_award'].search([
            ('award_id', '=', self.award_id.id),
            ('cantidad', '>', 0),
            ('partner_id.name', '!=', 'Consumidor Final')
        ])

        participants = []
        for award in partner_awards:
            participants.extend([award.partner_id.id] * award.cantidad)

        if participants:
            winner_partner_id = random.choice(participants)
            winner = self.env['res.partner'].browse(winner_partner_id)
            winner_award = partner_awards.filtered(lambda a: a.partner_id.id == winner.id)

            self.winner_id = winner.id
            self.winner_tickets = winner_award.cantidad if winner_award else 0
        else:
            raise UserError('No hay participantes válidos para este premio.')
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/sorteo/resultado/{self.id}',
            'target': 'self',
        }
