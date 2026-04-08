# -*- coding: utf-8 -*-

import uuid

from odoo import api, fields, models


class mass_create_share(models.TransientModel):
    """
    The model to keep attributes of mass update
    """
    _name = "mass.create.share"
    _description = "Share Attachments"

    @api.depends("access_token")
    def _compute_access_url(self):
        """
        Compute method for access url
        """
        for share in self:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            share.acess_url = "{}/clouds/share/token/{}".format(base_url, share.access_token)

    attachment_ids = fields.Many2many("ir.attachment", string="Shared attachments")
    folder_ids = fields.Many2many("clouds.folder", string="Extra Shared Folders")
    tag_ids = fields.Many2many("clouds.tag", string="Extra Shared Tags")
    share_method = fields.Selection(
        [("new_share", "Create a new share"), ("existing_share", "Add to an existing share")],
        string="Sharing",
        required=True,
        default="new_share",
    )
    share_id = fields.Many2one("clouds.share", string="Share to", ondelete="cascade")
    name = fields.Char(string="Name")
    partner_ids = fields.Many2many(
        "res.partner",
        "res_partner_mass_create_share_rel_table",
        "res_partner_id",
        "clouds_share_id",
        string="Portal Access",
    )
    allow_by_token = fields.Boolean(string="Access by Token")
    access_token = fields.Char(string="Access Token", default=lambda self: str(uuid.uuid4()))
    acess_url = fields.Char(string="Access Url", compute=_compute_access_url, store=False)
    active_till = fields.Datetime(string="Active Till")
    send_invitation = fields.Boolean(string="Send Invitation")

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overwrite to trigger attachments update
        The idea is to use standard 'Save' buttons and do not introduce its own footer for each mass action wizard

        Methods:
         * action_update_attachments
        """
        wizards = super(mass_create_share, self).create(vals_list)
        wizards.action_update_attachments()
        return wizards

    def action_update_attachments(self):
        """
        The method to update attachments in batch

        Methods:
         * _update_products
        """
        for wiz in self:
            if wiz.attachment_ids:
                wiz._update_attachments(wiz.attachment_ids)

    def _update_attachments(self, attachment_ids):
        """
        The method to update attachment shares

        Args:
         * attachment_ids - ir.attachment recordset

        Extra info:
         * Expected singleton
        """
        if self.share_method == "new_share":
            share_id = self.env["clouds.share"].create([{
                "name": self.name,
                "partner_ids": [(6, 0, self.partner_ids.ids)],
                "allow_by_token": self.allow_by_token,
                "access_token": self.access_token,
                "active_till": self.active_till,
                "folder_ids": [(6, 0, self.folder_ids.ids)],
                "tag_ids": [(6, 0, self.tag_ids.ids)],
            }])[0]
            if self.send_invitation and self.partner_ids:
                template = self.env.ref("cloud_base.clouds_share_invitation")
                messages = template._render_template_qweb(template.body_html, "clouds.share", [share_id.id])
                share_id.message_post(body=messages.get(share_id.id), partner_ids=self.partner_ids.ids)
        else:
            share_id = self.share_id
            share_id.write({
                "folder_ids": [(4, fol.id) for fol in self.folder_ids],
                "tag_ids": [(4, fol.id) for fol in self.tag_ids],
            })
        attachment_ids.write({"share_ids": [(4, share_id.id)]})
