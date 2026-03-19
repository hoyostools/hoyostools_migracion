from odoo import http
from odoo.http import request
from odoo.addons.helpdesk.controllers.portal import CustomerPortal


class PortalTicketFilter(CustomerPortal):

    def _prepare_helpdesk_tickets_domain(self):
        partner = request.env.user.partner_id

        # SOLO tickets del usuario logeado
        return [('partner_id', '=', partner.id)]