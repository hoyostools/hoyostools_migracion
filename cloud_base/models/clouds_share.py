# -*- coding: utf-8 -*-

import uuid

from odoo import api, fields, models


class clouds_share(models.Model):
    """
    The model to share attachments and folders
    """
    _name = "clouds.share"
    _inherit = ["clouds.node", "mail.activity.mixin", "mail.thread"]
    _description = "Clouds Share"

    @api.depends("attachment_ids", "folder_ids.attachment_ids", "tag_ids.attachment_ids")
    def _compute_shared_attachment_ids(self):
        """
        Compute method for shared_attachment_ids

        Methods:
         * action_get_share_folders
         * action_get_share_tags
        """
        for share in self:
            all_folder_ids = share.action_get_share_folders()
            all_tag_ids = share.action_get_share_tags()
            all_attachment_ids = share.attachment_ids | all_folder_ids.mapped("attachment_ids") \
                | all_tag_ids.mapped("attachment_ids")
            share.shared_attachment_ids = [(6, 0, all_attachment_ids.ids)]

    @api.depends("access_token")
    def _compute_access_url(self):
        """
        Compute method for access url
        """
        for share in self:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            share.acess_url = "{}/clouds/share/token/{}".format(base_url, share.access_token)

    parent_id = fields.Many2one("clouds.share", string="Parent Share")
    child_ids = fields.One2many("clouds.share", "parent_id", string="Child Shares")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "ir_attachment_clouds_share_rel_table",
        "ir_attachment_id",
        "clouds_share_id",
        string="Shared Attachments",
    )
    folder_ids = fields.Many2many(
        "clouds.folder",
        "clouds_folder_clouds_share_rel_table",
        "clouds_folder_id",
        "clouds_share_id",
        string="Shared Folders",
    )
    tag_ids = fields.Many2many(
        "clouds.tag",
        "clouds_tag_cloud_share_rel_table",
        "clouds_tag_id",
        "clouds_share_id",
        string="Shared Tags",
    )
    shared_attachment_ids = fields.Many2many(
        "ir.attachment",
        "ir_attachment_clouds_share_all_rel_table",
        "ir_attachment_id",
        "clouds_share_id",
        compute=_compute_shared_attachment_ids,
        store=False,
        string="All Attachments",
    )
    partner_ids = fields.Many2many(
        "res.partner",
        "res_partner_clouds_share_rel_table",
        "res_partner_id",
        "clouds_share_id",
        string="Portal Access",
    )
    allow_by_token = fields.Boolean(string="Access by Token")
    access_token = fields.Char(string="Access Token", default=lambda self: str(uuid.uuid4()))
    acess_url = fields.Char(string="Access Url", compute=_compute_access_url, store=False)
    active_till = fields.Datetime(string="Active Till")
    allow_uploading = fields.Boolean(string="Allow Uploading")
    uploading_folder_id = fields.Many2one(
        "clouds.folder",
        string="Uploading Folder",
        help="This folder will be selected by default to upload files from the portal",
    )
    show_folders = fields.Boolean(string="Show folders")
    allow_adding_folders = fields.Boolean(string="Allow adding folders")
    allow_folders_search = fields.Boolean(string="Allow searching folders")
    show_tags = fields.Boolean(string="Show tags")
    allow_adding_tags = fields.Boolean(string="Allow adding tags")
    allow_tags_search = fields.Boolean(string="Allow searching tags")
    show_chatter = fields.Boolean(string="Show Chat")
    allow_slideshow = fields.Boolean(string="Allow slideshow")

    def action_update_attachment(self, attachment):
        """
        The method to update attachment tags

        Args:
         * attachment - str (attachment_)

        Extra info:
         * We are in try/except to make sure that an excess node is removed
         * Expected singleton
        """
        try:
            attachment_int = int(attachment[11:])
            attachment_id = self.env["ir.attachment"].browse(attachment_int).exists()
            if self.exists() and attachment_id and self.id not in attachment_id.share_ids.ids:
                attachment_id.write({"share_ids": [(4, self.id)]})
        except:
            pass

    def action_get_share_folders(self):
        """
        The method to find all available folders and their child folders

        Returns:
         * clouds.folder recordser

        Extra info:
         * Expected singleton
        """
        all_folder_ids = self.folder_ids | self.uploading_folder_id
        child_ids = all_folder_ids.mapped("child_ids")
        while child_ids:
            all_folder_ids |= child_ids
            child_ids = child_ids.mapped("child_ids")
        return all_folder_ids

    def action_get_share_tags(self):
        """
        The method to find all available tags and their child tafs

        Returns:
         * clouds.tag recordset

        Extra info:
         * Expected singleton
        """
        all_tag_ids = self.tag_ids
        child_ids = all_tag_ids.mapped("child_ids")
        while child_ids:
            all_tag_ids |= child_ids
            child_ids = child_ids.mapped("child_ids")
        return all_tag_ids

    def action_preview(self):
        """
        The method to open the portal view

        Returns:
         * dict (action)

        Extra info:
         * Expected singleton
        """
        res = {"name": "Preview Portal", "type": "ir.actions.act_url", "url": "/clouds/share/{}".format(self.id)}
        return res

    def action_generate_token(self):
        """
        The method to generate access token
        """
        self.sudo().write({"access_token": str(uuid.uuid4())})

    @api.model
    def action_check_expired_shares(self):
        """
        The method to archive expired shares
        """
        expired_ids = self.search([("active_till", "<=", fields.Datetime.now())])
        if expired_ids:
            expired_ids.write({"active": False})

    def _check_active(self):
        """
        The method to check whether this share is active

        Returns:
         * bool

        Extra info:
         * Expected singleton
        """
        return self.active and (not self.active_till or self.active_till > fields.Datetime.now()) and True or False
