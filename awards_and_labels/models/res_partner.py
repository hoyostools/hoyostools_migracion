from odoo import models, fields
from odoo.exceptions import UserError
import threading
import time


class ResPartnerAward(models.Model):
    _name = 'awards_and_labels.res_partner_award'
    _description = 'Relación Partner Premio'
    _rec_name = 'award_id'

    partner_id = fields.Many2one('res.partner', string='Contacto', required=True, ondelete='cascade')
    award_id = fields.Many2one('awards_and_labels.award', domain=[('active', '=', True)], string='Premio', required=True, ondelete='cascade')
    cantidad = fields.Integer(string='Cantidad', default=0)
    historial = fields.Integer(string='Historial acumulado', default=0)
    
    def write(self, vals):
        for rec in self:
            changes = []
            if 'cantidad' in vals and rec.cantidad != vals['cantidad']:
                changes.append(f"Cantidad: {rec.cantidad} → {vals['cantidad']}")
            if 'historial' in vals and rec.historial != vals['historial']:
                changes.append(f"Historial: {rec.historial} → {vals['historial']}")

            result = super().write(vals)

            if changes:
                message = f"Se modificaron los siguientes valores en el premio '{rec.award_id.name}'" + "<br/>".join(changes)
                rec.partner_id.message_post(
                    body=message,
                    subtype_xmlid='mail.mt_note'
                )
        return result

class ResPartner(models.Model):
    _inherit = 'res.partner'

    award_ids = fields.One2many('awards_and_labels.res_partner_award', 'partner_id', string='Tiquetes Premios', domain=[('award_id.active', '=', True)],)

