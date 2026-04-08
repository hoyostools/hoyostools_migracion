# -*- coding: utf-8 -*-

from odoo import api, fields, models


class mass_update_tag(models.TransientModel):
    """
    The model to keep attributes of mass update
    """
    _name = "mass.update.tag"
    _description = "Update Tags"

    attachment_ids = fields.Many2many("ir.attachment", string="Updated attachments")
    to_add_tag_ids = fields.Many2many(
        "clouds.tag",
        "clouds_tag_mass_update_rel_table",
        "clouds_tag_id",
        "mass_update_id",
        string="Add Tags",
    )
    to_remove_tag_ids = fields.Many2many(
        "clouds.tag",
        "clouds_tag_mass_update_rel_remove_table",
        "clouds_tag_id",
        "mass_update_id",
        string="Remove Tags",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overwrite to trigger attachments update
        The idea is to use standard 'Save' buttons and do not introduce its own footer for each mass action wizard

        Methods:
         * action_update_attachments
        """
        wizards = super(mass_update_tag, self).create(vals_list)
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
        The method to update attachment tags

        Args:
         * attachment_ids - ir.attachment recordset

        Extra info:
         * Expected singleton
        """
        updated_tags = []
        if self.to_add_tag_ids:
            for tag in self.to_add_tag_ids:
                updated_tags.append((4, tag.id))
        if self.to_remove_tag_ids:
            for tag in self.to_remove_tag_ids:
                updated_tags.append((3, tag.id))
        if updated_tags:
            attachment_ids.write({"cloud_tag_ids": updated_tags})
