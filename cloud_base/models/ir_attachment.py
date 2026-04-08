# -*- coding: utf-8 -*-

import io
import zipfile

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.http import content_disposition


FORBIDDENSYMBOLS = ['~', '#', '&', ':', '{', '}', '*', '?', '"', "'", '<', '>', '|', '+', '%', '!', '@', '\\', '/']
SPECIAL_MIMETYPES = [
    "application/vnd.google-apps.spreadsheet", "application/vnd.google-apps.document",
    "application/vnd.google-apps.presentation",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
]
FOLDER_MIMETYPES = ["application/vnd.google-apps.folder", "dir"]
NOT_SYNCED_MIMETYPES = ["text/html", "text/css", "text/javascript", "application/javascript", "text/xml",
    "application/xml"]
IMAGE_MIMETYPES = ["image/bmp", "image/gif", "image/jpeg", "image/png", "image/svg+xml", "image/tiff", "image/x-icon",
    "image/webp"]
MAX_NAME_LEN = 180

def check_allowed_mimetypes(mimetype):
    """
    This mimetype is required only for "special" mimetypes. Standard ones are defined by Odoo
    """
    available_mimetypes = SPECIAL_MIMETYPES + FOLDER_MIMETYPES
    if not mimetype or mimetype not in (SPECIAL_MIMETYPES + FOLDER_MIMETYPES):
        mimetype = False
    elif mimetype in FOLDER_MIMETYPES:
        mimetype = "special_cloud_folder"
    return mimetype


class ir_attachment(models.Model):
    """
    Overwritting to prepare method for cloud api methods

    When use:
     * Introduce to-implement methods (in the bottom)
     * Try to optimize cron_synchronize_attachments_backward if sth like "track changes" method exists in a client

    Extra info:
     * in comparison to folders we do not remove illegal characters and do not make titles unique assuming that
       it would be done in queue, since:
        (a) it is very bad for performace while installing the app and during any attachment upload
        (b) we do not assume that backward renaming would make any change in Odoo
    """
    _inherit = "ir.attachment"

    @api.depends("store_fname", "db_datas")
    def _compute_raw(self):
        """
        Fully re-write core function to pass cloud_key to file-read
        """
        for attach in self:
            if attach.type == "url" and attach.cloud_key:
                try:
                    attach.raw = self._file_read(attach.store_fname, attach)
                except Exception as er:
                    attach.raw = False
            elif attach.store_fname:
                attach.raw = attach._file_read(attach.store_fname)
            else:
                attach.raw = attach.db_datas

    def _inverse_datas(self):
        """
        Overwrite to avoid writing on cloud datas into Odoo
        """
        for attach in self:
            if not attach.cloud_key:
                super(ir_attachment, attach)._inverse_datas()

    def _inverse_raw(self):
        """
        Overwrite to avoid writing on cloud datas into Odoo
        """
        for attach in self:
            if not attach.cloud_key:
                super(ir_attachment, attach)._inverse_raw()

    for_delete = fields.Boolean(default=False, string="Marked for delete")
    active = fields.Boolean(string="Active", default=True)
    clouds_folder_id = fields.Many2one("clouds.folder", string="Folder", index=True, ondelete="set null")
    sync_cloud_folder_id = fields.Many2one("clouds.folder", string="Folder used for sync")
    sync_client_id = fields.Many2one("clouds.client", string="Client used for sync")
    cloud_key = fields.Char(string="Cloud key", copy=False)
    cloud_tag_ids = fields.Many2many(
        "clouds.tag",
        "clouds_tag_ir_attachment_rel_table",
        "tag_id",
        "ir_attachment_id",
        string="Tags",
    )
    share_ids = fields.Many2many(
        "clouds.share",
        "ir_attachment_clouds_share_rel_table",
        "clouds_share_id",
        "ir_attachment_id",
        string="Shares",
    )
    color = fields.Integer(string="Color")
    # introduced for inheritance purposes to filter not-syncing attachments
    handler = fields.Char(string="Handler")
    url = fields.Char(size=4096) # with very long names, sync URL might be also very long

    ####################################################################################################################
    ##################################   CORE methods   ################################################################
    ####################################################################################################################
    @api.model
    def check(self, mode, values=None):
        """
        Re-write to pass context for clouds.folder reference
        """
        super(ir_attachment, self.with_context(ir_attachment_security=True)).check(mode=mode, values=values)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Re-write to make sure that if an attachment has a linked record it would immediately linked to its folder

        Methods:
         * _get_res_params_by_folder
         * _get_folder_by_res_params
        """
        folder_id = self._context.get("cc_folder_id")
        for values in vals_list:
            if folder_id:
                values.update({"clouds_folder_id": folder_id})
            if values.get("clouds_folder_id"):
                values.update(self._get_res_params_by_folder(values.get("clouds_folder_id")))
            else:
                values.update(self._get_folder_by_res_params(values.get("res_model"), values.get("res_id")))
        return super(ir_attachment, self).create(vals_list)

    def write(self, vals):
        """
        Re-write to change attachment values if folder is changed
         1. If folder is updated to False > need to unlink attachment from an object

        Methods:
         * _get_res_params_by_folder

        Extra info:
         * context args "no_folder_update" should be passed each time a brand new (not commited) clouds folder
           is created and then linked to attachment (exactly through auto folders' preparation)
         * here we do not check for res_id, res_model changes, since it actually happen only for mail attachments
           (see mail_thread), while here it would trigger recursive issues
        """
        folder_id = False
        if not self._context.get("no_folder_update") and vals.get("clouds_folder_id") is not None:
            if vals.get("clouds_folder_id"):
                update_vals = self._get_res_params_by_folder(vals.get("clouds_folder_id"), True)
                vals.update(update_vals)
            else:
                # 1
                vals.update({"res_model": False, "res_id": 0})
        return super(ir_attachment, self).write(vals)

    def unlink(self):
        """
        Overwite unlink to guarantee that a synced attachment would be deleted only after deletion is done per client
        Normal not synced attachment (with cloud_key) are deleted right there

        Synced attachments are deleted as 2 steps-process:
         1. Firstly mark for delete
         2. During the next unlink - delete an item (might happen only explicitly)

        Extra info:
         * we make extra check for rights, since "writing" for_delete is also unlink, not "write"
        """
        if not self:
            return True
        self.check("unlink")
        for_delete = self.filtered(lambda at: at.for_delete or not at.cloud_key)
        mark_for_delete = self - for_delete
        mark_for_delete.write({"for_delete": True, "active": False})
        result = super(ir_attachment, for_delete).unlink()
        return result

    def _file_delete_special(self, fname):
        """
        The special method to remove file, since store_fnameis not any more writeable
        """
        self._file_delete(fname)
        query = "UPDATE ir_attachment SET store_fname = NULL WHERE id = %s"
        self._cr.execute(query, (self.id,))
        self._cr.commit()

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        """
        Re-write to pass context for clouds.folder reference
        """
        return super(ir_attachment, self.with_context(ir_attachment_security=True))._search(
            domain, offset, limit, order, access_rights_uid
        )

    def copy(self, default=None):
        """
        Overwrite to make proper copy when synced or deleted
        """
        self.check("write")
        default = default or {}
        default.update({"for_delete": False, "cloud_key": False})
        if (default.get("res_model") or default.get("res_id")) and not default.get("clouds_folder_id"):
            default.update({"clouds_folder_id": False})
            self = self.with_context(cc_folder_id=False)
        return super(ir_attachment, self).copy(default)

    @api.model
    def _file_read(self, fname, attach_cloud_id=False):
        """
        Rewrite to read files from Cloud client

        Extra Args:
         * attach_cloud_id - ir.attachment object

        Extra Methods:
         * _return_client_context of clouds.client
         * _upload_attachment_from_cloud
        """
        if not attach_cloud_id:
            r = super(ir_attachment, self)._file_read(fname=fname)
        else:
            r = attach_cloud_id.sudo()._upload_attachment_from_cloud()
            if not r:
                raise ValidationError(_("Unexpected error: binary content cannot be retrieved from clouds"))
        return r

    def action_retrieve_url(self):
        """
        The method to retrieve a topical URL
        It is introduced for the case when a cloud client have a relative path in their links and might be changed

        Methods:
         * _retrieve_url of clouds.client

        Returns:
         * char

        Extra info:
         * Expected singleton
        """
        return self.sync_client_id and self.cloud_key \
            and self.sync_client_id._retrieve_url(self) or self.url or False

    def action_retrieve_url_window(self):
        """
        The method to return the window action for the url opening

        Methods:
         * action_retrieve_url

        Returns:
         * dict

        Extra info:
         * Expected singleton
        """
        return {
            "name": "{}".format(self.name),
            "type": "ir.actions.act_url",
            "url": self.action_retrieve_url(),
        }

    def _attachment_format(self):
        """
        Re-write to pass cloud parameters
        """
        res_list = super(ir_attachment, self)._attachment_format()
        for res_dict in res_list:
            attachment_id = self.env["ir.attachment"].browse(res_dict.get("id"))
            res_dict.update({
                "cloudSynced": attachment_id.cloud_key and True or False,
                "cloudURL": attachment_id.url or False,
                "forDelete": attachment_id.for_delete,
            })
        return res_list

    def action_return_all_pages_ids(self, domain):
        """
        The method to search attachments by js domain

        Returns:
         *  list of all selected attachments
        """
        all_attachments = set(self.ids + self.search(domain).ids)
        return list(all_attachments)

    def action_get_images(self, core_url="/web/content/{}"):
        """
        The method to get only attachments that are images

        Args:
         * core_url - string to format attachment image

        Returns:
         * list of strings (get binary URLs)

        Raises:
         * ValidationError - if no ids or no images found
        """
        error_message = _("There are no images selected!")
        if not self:
            raise ValidationError(error_message)
        images = []
        for attachment in self:
            if attachment.mimetype in IMAGE_MIMETYPES and (attachment.type != "url" or attachment.cloud_key):
                images.append(core_url.format(attachment.id))
        if not images:
            raise ValidationError(error_message)
        return images

    def _download_as_archive(self, archive_name=None):
        """
        The method to prepare and header for downloading attachments as zip

        Args:
         * archive_name - str

        Methods:
         * _get_stream_from of ir.binary

        Returns:
         * tuple
          ** content
          ** headers (list)
        """
        stream = io.BytesIO()
        try:
            with zipfile.ZipFile(stream, "w") as zip_archive:
                for attachment_id in self:
                    if attachment_id.type == "binary" or (attachment_id.type == "url" and attachment_id.cloud_key):
                        binary_stream = self.env["ir.binary"]._get_stream_from(attachment_id, "raw")
                        zip_archive.writestr(
                            binary_stream.download_name, binary_stream.read(), compress_type=zipfile.ZIP_DEFLATED
                        )
        except zipfile.BadZipfile:
            pass
        content = stream.getvalue()
        archive_title = archive_name or "odoo_{}".format(fields.Datetime.now())
        headers = [
            ("Content-Type", "zip"),
            ("X-Content-Type-Options", "nosniff"),
            ("Content-Length", len(content)),
            ("Content-Disposition", content_disposition("{}.zip".format(archive_title)))
        ]
        return content, headers

    def _download_as_attachment(self):
        """
        The method to prepare and header for downloading attachment

        Methods:
         * _get_stream_from of ir.binary

        Returns:
         * tuple
          ** content
          ** headers (list)

        Extra info:
         * Expected singleton
        """
        content, headers = False, False
        if self.type == "binary" or (self.type == "url" and self.cloud_key):
            binary_stream = self.env["ir.binary"]._get_stream_from(self, "raw")
            send_file_kwargs = {"as_attachment": True, "max_age": None}
            res = binary_stream.get_response(**send_file_kwargs)
            res.headers["Content-Security-Policy"] = "default-src 'none'"
        return res

    def _upload_attachment_from_cloud(self):
        """
        Method to upload attachment from cloud

        Methods:
         * _upload_attachment_from_cloud of clouds.client
         * _return_specific_client_context of clouds.client

        Returns:
         * Binary File
         * False if method failed

        Extra info:
         * Expected singleton
        """
        ctx = self._context.copy()
        cfolder = self.sync_cloud_folder_id or self.clouds_folder_id
        cclient = cfolder.client_id
        if "cclients" not in ctx.keys():
            new_ctx = cclient.sudo()._return_specific_client_context()
            ctx.update(new_ctx)
        self = self.with_context(ctx)
        cfolder = self.sync_cloud_folder_id or self.clouds_folder_id
        cclient = cfolder.client_id
        return cclient._upload_attachment_from_cloud(cfolder, self, self.cloud_key, {})

    def _get_res_params_by_folder(self, cloud_folder_id, from_write=False):
        """
        The method to caclulate res_model and res_param by updated folder
         1. Attachments with res_model, but without res_id do not pass security checks > so, we write cloud_folder
            own id and its model name
         2. We also check the very special case - of attachment linked to document.document, since such attachment
            relates not to a worskpace, but a document itself. So, we should not change its res_model & res_id
         3. If we write a new "empty" folder, we unlink that attachment from object

        Args:
         * cloud_folder_id - int
         * from_write - bool - whether we come from write

        Returns:
         * dict:
          ** res_model - str
          ** res_id - int
        """
        updated_values = {}
        real_folder_id = isinstance(cloud_folder_id, int) and cloud_folder_id or int(cloud_folder_id)
        folder_id = self.sudo().env["clouds.folder"].browse(real_folder_id).exists()
        if folder_id:
            if not folder_id.res_id:
                # 1
                updated_values.update({"res_model": "clouds.folder", "res_id": folder_id.id})
            else:
                if folder_id.res_model == "documents.folder":
                    # 2
                    pass
                else:
                    updated_values.update({"res_model": folder_id.res_model, "res_id": folder_id.res_id})
        elif from_write:
            # 3
            updated_values.update({"res_model": False, "res_id": 0})
        return updated_values

    def _get_folder_by_res_params(self, res_model, res_id):
        """
        The method to find a folder for updated attachment. Used when folder is not in vals

        Args:
         * res_model - str
         * res_id - int

        Returns:
         * dict
          ** clouds_folder_id - int
        """
        updated_values = {}
        if res_model and res_id:
            res_domain = [("res_id", "=", res_id), ("res_model", "=", res_model)]
            folder_id = self.sudo().with_context(active_test=False).env["clouds.folder"].search(res_domain, limit=1)
            if folder_id:
                updated_values = {"clouds_folder_id": folder_id.id}
        return updated_values

    ####################################################################################################################
    ##################################   SYNC-related helpers ##########################################################
    ####################################################################################################################
    def _filter_non_synced_attachments(self):
        """
        The method to filter system attachments

        Retunrs:
         * ir.attachment recordset
        """
        mime_types = NOT_SYNCED_MIMETYPES
        mime_types_conf = self.env["ir.config_parameter"].sudo().get_param("cloud_base.notsynced_mimetypes", "")
        if mime_types_conf:
            mime_types += mime_types_conf.split(",")
        attachments = self
        for attachment in self:
            if attachment.handler or attachment.mimetype in mime_types  \
                    or (attachment.type == "url" and not attachment.cloud_key) \
                    or attachment.name.startswith("/") or (attachment.url and attachment.url.startswith("/")) \
                    or attachment.res_field:
                attachments -= attachment
        return attachments

    @api.model
    def _remove_illegal_characters(self, s, safe_name="NOT CORRECT NAME", check_extension=False):
        """
        The method to replace not safe file system characters

        Args:
         * s - string
         * safe_name - what should be used instead of name, if method results in empty string
         * check_extension - bool - whether in case of big name size, we should consider extension not to be cut

        Returns:
         * s - string

        Extra info:
         * The method is not global to use in all Clients
         * We cut the item name if it is has too long name; since we cannot control path length, we apply
           each time shortening:
           ** Dropbox - 255 for each item name (not full path): https://github.com/dropbox/dropbox-sdk-java/issues/229
           ** Owncloud - seems to be some 227 symbols (experimentally, but not totally sure)
           OS filesystem might have also their own limits (ubuntu has default config for 255 symbols); Windows
           block 260bytes paths
           So, with adding tolerance it's decided to cut 180-long items
        """
        def find_index_dot(s_list):
            """
            The method to find dot

            Args:
             * s_list - str

            Returns:
             * int - number of the first dot in string
            """
            start = 0
            for symbol in s_list:
                if symbol in [".", " "]:
                    start += 1
                else:
                    break
            return start

        # to make sure item name is not empty
        s = s or safe_name
        # to replace dangerous symboles from item name
        for symbol in FORBIDDENSYMBOLS:
            s = s.replace(symbol, "-")
        # remove space and dots at the beginning and at the end if any
        start = find_index_dot(s)
        end = find_index_dot(reversed(s))
        if start:
            s = s[start:]
        if end:
            s = s[:-end]
        # final checks
        if len(s) > MAX_NAME_LEN:
            # cut too big names
            if not check_extension:
                # if not extension, just remove the last symbols
                s = s[:MAX_NAME_LEN]
            else:
                last_dot = s.rfind(".")
                if last_dot == -1 or (len(s)-last_dot > 50):
                    # no dot or extension is too big
                    s = s[:MAX_NAME_LEN]
                else:
                    s1 = s[:last_dot]
                    s2 = s[last_dot:]
                    s1 = s1[:MAX_NAME_LEN-len(s2)]
                    s = s1 + s2
        else:
            # make sure final element is not empty
            s = s or safe_name
        return s
