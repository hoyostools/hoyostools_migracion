# -*- coding: utf-8 -*-

from odoo import Command, models


class mail_thread(models.AbstractModel):
    """
    Overwrite to make sure attatchments updated through emails will have correct folder
    We should not do that in "write" since it will be recursive update
    """
    _inherit = "mail.thread"

    def _process_attachments_for_post(self, attachments, attachment_ids, message_values):
        """
        Overwrite to pass "clouds_folder_id" to attachments

        Returns:
         * list of dicts per each message in the format for web client
        """
        m2m_attachment_ids = []
        if attachment_ids:
            model = message_values["model"]
            res_id = message_values["res_id"]
            filtered_attachment_ids = self.env["ir.attachment"].sudo().browse(attachment_ids).filtered(
                lambda a: a.res_model == "mail.compose.message" and a.create_uid.id == self._uid
            )
            if filtered_attachment_ids:
                values = {"res_model": model, "res_id": res_id}
                res_domain = [("res_id", "=", res_id), ("res_model", "=", model)]
                folder_id = self.sudo().with_context(active_test=False).env["clouds.folder"].search(res_domain, limit=1)
                if folder_id:
                    values.update({"clouds_folder_id": folder_id.id})
                filtered_attachment_ids.sudo().write(values)
                m2m_attachment_ids = [Command.link(id) for id in filtered_attachment_ids.ids]
        return_values = super(mail_thread, self)._process_attachments_for_post(
            attachments=attachments, attachment_ids=attachment_ids, message_values=message_values,
        )
        if not self.env.user.has_group("base.group_user") and m2m_attachment_ids:
            # Since we already wrote on attachments, they would be filtered in super, so we need to add them manually
            parent_attachments = return_values.get("attachment_ids") or []
            return_values.update({"attachment_ids": parent_attachments + m2m_attachment_ids})
        return return_values
