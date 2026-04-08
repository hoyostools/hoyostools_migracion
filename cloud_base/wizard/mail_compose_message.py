# -*- coding: utf-8 -*-

from odoo import fields, models


class mail_compose_message(models.TransientModel):
    """
    Overwrite to make it possible to select existing attachments (including the synced ones)
    """
    _inherit = "mail.compose.message"

    existing_attachment_ids = fields.Many2many(
        "ir.attachment",
        "ir_attachment_mail_compose_message_rel_table",
        "mail_compose_message_id",
        "ir_attachment_id",
        string="Existing Attachments",
    )

    def _prepare_mail_values(self, res_ids):
        """
        Overwrite to make it possible to select existing attachments (including the synced ones)
        """
        mail_values_all = super(mail_compose_message, self)._prepare_mail_values(res_ids=res_ids)
        if self.existing_attachment_ids:
            for message_vals in mail_values_all.values():
                new_attachment_ids = message_vals.get("attachment_ids") or []
                new_attachment_ids.extend(self.existing_attachment_ids.ids)
                message_vals.update({"attachment_ids": new_attachment_ids})
        return mail_values_all
