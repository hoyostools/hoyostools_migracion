# -*- coding: utf-8 -*-

from odoo import fields, models


class add_url_attachment(models.TransientModel):
    """
    The wizard to add an attachment of the type URL
    """
    _name = "add.url.attachment"
    _description = "Add Url"

    res_model = fields.Char(string="Res Model", required=False)
    res_id = fields.Char(string="Res ID", required=False)
    folder_id = fields.Many2one("clouds.folder", string="Folder")
    name = fields.Char(string="Attachment Name", required=True)
    url = fields.Char(string="Url", required=True)

    def action_link_attachment(self):
        """
        The method to create an attachment and link it to the target model

        Methods:
         * _clean_website or res.partner
        """
        vals = {
            "type": "url",
            "name": self.name,
            "url": self.env["res.partner"]._clean_website(self.url),
        }
        if self.folder_id:
            vals.update({"clouds_folder_id": self.folder_id.id})
        else:
            vals.update({"res_model": self.res_model, "res_id": self.res_id})
        self = self.with_context({"default_folder_id": False})
        attachment_ids = self.env["ir.attachment"].create([vals])
        return attachment_ids
