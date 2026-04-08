# -*- coding: utf-8 -*-

import base64
import json
import unicodedata

from odoo import _, fields, http
from odoo.addons.mail.controllers.attachment import AttachmentController
from odoo.addons.mail.models.discuss.mail_guest import add_guest_to_context
from odoo.addons.web.controllers.binary import clean
from odoo.exceptions import AccessError
from odoo.http import content_disposition, request
from odoo.tools import replace_exceptions


class cloudFiles(AttachmentController):
    """
    Controller to manage attachments operations in file manager
    """
    @http.route("/mail/attachment/upload", methods=["POST"], type="http", auth="public")
    @add_guest_to_context
    def mail_attachment_upload(self, ufile, thread_id, thread_model, is_pending=False, **kwargs):
        """
        Re-write to get cloud folder from kwargs if any
        """
        lcl_ctx = request.env.context.copy()
        lcl_ctx.update({"cc_folder_id": kwargs.get("clouds_folder_id")})
        request.env = request.env(context=lcl_ctx)
        return super(cloudFiles, self).mail_attachment_upload(ufile, thread_id, thread_model, is_pending, **kwargs)

    @http.route("/cloud_base/folder", methods=["POST"], type="json", auth="user")
    def cloud_base_check_object_folder(self, thread_model, thread_id, **kwargs):
        """
        The method calculate whether thread has a linked folder

        Returns:
         * bool
        """
        folder_count = 0
        if thread_id and thread_model:
            folder_count = request.env["clouds.folder"].search_count(
                [("res_model", "=", thread_model), ("res_id", "=", thread_id)], limit=1
            )
        return folder_count and True or False

    @http.route("/cloud_base/attachments/data", methods=["POST"], type="json", auth="user")
    def cloud_base_folder_attachments(self, thread_model, thread_id, checked_folder, folder_domain, **kwargs):
        """
        The method to format attachments

        Methods:
         * _attachment_format of ir.attachment

        Returns:
         * list of dicts
        """
        thread = request.env[thread_model].with_context(active_test=False).search([("id", "=", thread_id)])
        f_domain = folder_domain
        if not checked_folder:
            f_domain = [("res_id", "=", thread_id), ("res_model", "=", thread_model)]
        return request.env["ir.attachment"].search(f_domain, order="id desc")._attachment_format()

    @http.route("/cloud_base/upload_attachment", type="http", auth="user")
    def upload_to_file_manager(self, clouds_folder_id, ufile, callback=None):
        """
        The method to create folder-related attachment based on uploaded file
        @see web/controllers/binary > upload_attachment
        """
        out = """<script language="javascript" type="text/javascript">
            var win = window.top.window;
            win.jQuery(win).trigger(%s, %s);
        </script>"""
        args = []
        if not clouds_folder_id or clouds_folder_id == "false":
            args.append({"error": _("Please select a folder for uploaded files")})
        else:
            files = request.httprequest.files.getlist("ufile")
            Model = request.env["ir.attachment"]
            for ufile in files:
                filename = ufile.filename
                if request.httprequest.user_agent.browser == "safari":
                    filename = unicodedata.normalize("NFD", ufile.filename)
                try:
                    attachment = Model.create({
                        "name": filename,
                        "datas": base64.encodebytes(ufile.read()),
                        "clouds_folder_id": clouds_folder_id,
                    })
                    attachment._post_add_create()
                except AccessError:
                    args.append({"error": _("You are not allowed to upload an attachment here.")})
                except Exception:
                    args.append({"error": _("Something horrible happened")})
                else:
                    args.append({
                        "filename": clean(filename),
                        "mimetype": ufile.content_type,
                        "id": attachment.id,
                        "size": attachment.file_size
                    })
        return out % (json.dumps(clean(callback)), json.dumps(args)) if callback else json.dumps(args)

    @http.route(["/cloud_base/multiupload/<string:attachments>"], type="http", auth="user")
    def multi_download_file_manager(self, attachments, **kwargs):
        """
        The method to download multiple files as a zip archive

        Methods:
         * _download_as_archive of ir.attachment
        """
        attachment_ids = request.env["ir.attachment"]
        if attachments:
            attachment_ids = attachments.split(",")
            attachment_ids = request.env["ir.attachment"].browse([int(art) for art in attachment_ids]).exists()
        content, headers = attachment_ids._download_as_archive()
        return request.make_response(content, headers)

    @http.route(["/cloud_base/folder_upload/<model('clouds.folder'):folder_id>"], type="http", auth="user")
    def folder_download_file_manager(self, folder_id, **kwargs):
        """
        The method to prepare cloud folder attachments for downloading

        Methods:
         * _download_as_archive of ir.attachment
        """
        attachment_ids = request.env["ir.attachment"].search([("clouds_folder_id", "=", folder_id.id)])
        content, headers = attachment_ids._download_as_archive(folder_id.name)
        return request.make_response(content, headers)

    @http.route(["/cloud_base/share_upload/<model('clouds.share'):share_id>"], type="http", auth="user")
    def share_download_file_manager(self, share_id, **kwargs):
        """
        The method to prepare taf attachments for downloading

        Methods:
         * _download_as_archive of ir.attachment
        """
        content, headers = share_id.shared_attachment_ids._download_as_archive(share_id.name)
        return request.make_response(content, headers)

    @http.route(["/cloud_base/tag_upload/<model('clouds.tag'):tag_id>"], type="http", auth="user")
    def tag_download_file_manager(self, tag_id, **kwargs):
        """
        The method to prepare taf attachments for downloading

        Methods:
         * _download_as_archive of ir.attachment
        """
        attachment_ids = request.env["ir.attachment"].search([("cloud_tag_ids", "=", tag_id.id)])
        content, headers = attachment_ids._download_as_archive(tag_id.name)
        return request.make_response(content, headers)

    @http.route(["/cloud_base/export_logs"], type="http", auth="user")
    def cloud_base_export_logs(self, search_name, selected_clients, log_levels, period):
        """
        The method to prepare txt files with logs

        Methods:
         * _prepare_txt_logs
        """
        content = request.env["clouds.log"]._prepare_txt_logs(
            search_name, json.loads(selected_clients), json.loads(log_levels), json.loads(period),
        ).encode("utf-8")
        headers = [
            ("Content-Type", "zip"),
            ("X-Content-Type-Options", "nosniff"),
            ("Content-Length", len(content)),
            ("Content-Disposition", content_disposition("cloud_base_{}.logs".format(fields.Datetime.now())))
        ]
        return request.make_response(content, headers)
