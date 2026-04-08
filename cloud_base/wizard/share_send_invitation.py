# -*- coding: utf-8 -*-

from odoo import api, fields, models


class share_send_invitation(models.TransientModel):
    """
    The model to define new supplier details
    """
    _name = "share.send.invitation"
    _description = "Send Invitation"

    @api.depends("share_id")
    def _compute_message(self):
        """
        Default method for message
        """
        template = self.env.ref("cloud_base.clouds_share_invitation")
        messages = template._render_template_qweb(template.body_html, "clouds.share", self.mapped("share_id.id"))
        for invitation in self:
            invitation.message = messages.get(invitation.share_id.id)

    share_id = fields.Many2one("clouds.share", string="Share", required=True)
    partner_ids = fields.Many2many("res.partner", string="Portal Access", required=True)
    message = fields.Html(
        string="Message",
        compute=_compute_message,
        store=True,
        readonly=False,
        required=True,
        sanitize_style=True,
    )

    def action_send_invitation(self):
        """
        The method to share an invitation

        Extra info:
         * Expected singleton
        """
        partner_vals = [(4, partner.id) for partner in self.partner_ids]
        self.share_id.write({"partner_ids": partner_vals})
        self.share_id.message_post(body=self.message, partner_ids=self.partner_ids.ids)
