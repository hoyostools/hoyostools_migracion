# -*- coding: utf-8 -*-

from odoo import api, fields, models


class mass_attachment_update(models.TransientModel):
    """
    The model to keep attributes of mass update
    """
    _name = "mass.attachment.update"
    _description = "Update Attachments"

    attachment_ids = fields.Many2many("ir.attachment", string="Updated attachments")
    folder_id = fields.Many2one("clouds.folder", string="New folder")

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overwrite to trigger attachments update
        The idea is to use standard 'Save' buttons and do not introduce its own footer for each mass action wizard

        Methods:
         * action_update_attachments
        """
        wizards = super(mass_attachment_update, self).create(vals_list)
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
        The method to update attachment folder

        Args:
         * attachment_ids - ir.attachment recordset

        Extra info:
         * Expected singleton
        """
        attachment_ids.write({"clouds_folder_id": self.folder_id.id})
