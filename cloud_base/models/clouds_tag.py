# -*- coding: utf-8 -*-

from odoo import fields, models


class clouds_tag(models.Model):
    """
    The model to systemize cloud tags
    """
    _name = "clouds.tag"
    _inherit = ["clouds.node"]
    _description = "Tag"

    parent_id = fields.Many2one("clouds.tag", string="Parent Tag")
    child_ids = fields.One2many("clouds.tag", "parent_id", string="Child Tags")
    color = fields.Integer(string="Color index", default=10)
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "clouds_tag_ir_attachment_rel_table",
        "ir_attachment_id",
        "tag_id",
        string="Attachments",
    )

    _order = "sequence, id"

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
            if self.exists() and attachment_id and self.id not in attachment_id.cloud_tag_ids.ids:
                attachment_id.write({"cloud_tag_ids": [(4, self.id)]})
        except:
            pass
