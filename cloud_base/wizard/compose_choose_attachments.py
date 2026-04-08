# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class compose_choose_attachments(models.TransientModel):
    """
    The wizard to quick search attachments and add those to the message composer
    """
    _name = "compose.choose.attachments"
    _description = "Add Attachments"

    @api.model
    def _default_folder_ids(self):
        """
        Default method for tag_ids

        Methods:
         * action_return_tags_for_document of knowsystem.tag

        Returns:
         * list of ints
        """
        folder_ids = self.env["clouds.folder"]
        clouds_model = self._context.get("clouds_model")
        clouds_res_ids = self._context.get("clouds_res_ids")
        if clouds_model and clouds_res_ids:
            if not isinstance(clouds_res_ids, list):
                clouds_res_ids = safe_eval(self._context.get("clouds_res_ids"))
            folder_ids = self.env["clouds.folder"].search([
                ("res_model", "=", clouds_model), ("res_id", "in", clouds_res_ids),
            ])
        return folder_ids.ids

    @api.depends("name", "mimetype", "folder_ids", "tag_ids", "selected_attachment_ids")
    def _compute_attachment_ids(self):
        """
        Compute method for article_ids
        """
        for wizard in self:
            domain = wizard._get_domain()
            attachment_ids = self.env["ir.attachment"]._search(domain)
            wizard.attachment_ids = [(6, 0, attachment_ids)]

    name = fields.Char(string="Search in contents")
    mimetype = fields.Char(string="Search in mimetype")
    folder_ids = fields.Many2many(
        "clouds.folder",
        "clouds_folder_mail_compose_message_rel_table",
        "compose_choose_attachments_id",
        "clouds_folder_id",
        string="Folders",
        default=_default_folder_ids,
    )
    tag_ids = fields.Many2many(
        "clouds.tag",
        "clouds_tag_mail_compose_message_rel_table",
        "compose_choose_attachments_id",
        "clouds_tag_id",
        string="Tags",
    )
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments", compute=_compute_attachment_ids)
    selected_attachment_ids = fields.Many2many(
        "ir.attachment",
        "ir_attachment_article_search_selected_rel_table",
        "compose_choose_attachments_id",
        "attachment_id",
        string="Selected Attachments",
    )

    def _get_domain(self):
        """
        The method to get wizard domain based on introduced field values

        Returns:
         * list - RPR
        """
        domain = ["|", ("type", "=", "binary"), ("cloud_key", "!=", False)]
        if self.selected_attachment_ids:
            domain += [("id", "not in", self.selected_attachment_ids.ids)]
        if self.folder_ids:
            domain += [("clouds_folder_id", "child_of", self.folder_ids.ids)]
        if self.tag_ids:
            domain += [("cloud_tag_ids", "child_of", self.tag_ids.ids)]
        if self.name:
            domain += ["|", ("name", "ilike", self.name), ("index_content", "ilike", self.name)]
        if self.mimetype:
            domain += [("mimetype", "ilike", self.mimetype)]
        return domain
