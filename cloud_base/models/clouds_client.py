# -*- coding: utf-8 -*-

import json
import os
import shutil
import subprocess
import tempfile
from datetime import timedelta

import odoo
from odoo import _, api, fields, models, sql_db
from odoo.exceptions import ValidationError
from odoo.tools import config, exec_pg_environ, find_pg_tool, osutil

ICON_CLIENTS = {
    "google_drive": "/cloud_base/static/images/googledrive",
    "onedrive": "/cloud_base/static/images/onedrive",
    "sharepoint": "/cloud_base/static/images/sharepoint",
    "owncloud": "/cloud_base/static/images/owncloud",
    "nextcloud": "/cloud_base/static/images/nextcloud",
    "dropbox": "/cloud_base/static/images/dropbox",
}
METHODS_CLIENTS = {
    "google_drive": "google_drive",
    "onedrive": "onedrive",
    "sharepoint": "onedrive",
    "owncloud": "owncloud",
    "nextcloud": "owncloud",
    "dropbox": "dropbox",
}

def dump_db_manifest(cr):
    """
    Re-write from services.db to avoid the decorator check_db_management_enabled
    """
    pg_version = "%d.%d" % divmod(cr._obj.connection.server_version / 100, 100)
    cr.execute("SELECT name, latest_version FROM ir_module_module WHERE state = 'installed'")
    modules = dict(cr.fetchall())
    manifest = {
        'odoo_dump': '1',
        'db_name': cr.dbname,
        'version': odoo.release.version,
        'version_info': odoo.release.version_info,
        'major_version': odoo.release.major_version,
        'pg_version': pg_version,
        'modules': modules,
    }
    return manifest

def dump_db(db_name, stream, backup_format="zip", filestore=True, manifest=False):
    """
    Re-write from services.db to avoid the decorator check_db_management_enabled
    """
    cmd = [find_pg_tool("pg_dump"), "--no-owner", db_name]
    env = exec_pg_environ()
    with tempfile.TemporaryDirectory() as dump_dir:
        if filestore:
            filestore = config.filestore(db_name)
            if os.path.exists(filestore):
                shutil.copytree(filestore, os.path.join(dump_dir, "filestore"))
        if manifest:
            with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
                db = odoo.sql_db.db_connect(db_name)
                with db.cursor() as cr:
                    json.dump(dump_db_manifest(cr), fh, indent=4)
        cmd.insert(-1, "--file=" + os.path.join(dump_dir, "dump.sql"))
        subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
        if stream:
            osutil.zip_dir(dump_dir, stream, include_dir=False, fnct_sort=lambda file_name: file_name != "dump.sql")
        else:
            t = tempfile.TemporaryFile()
            osutil.zip_dir(dump_dir, t, include_dir=False, fnct_sort=lambda file_name: file_name != "dump.sql")
            t.seek(0)
            return t

class clouds_client(models.Model):
    """
    The model to keep connection settings
    It should be inherited in each linked connector and should specify:
     * cloud_client value(s). Use key as on the dict ICON_CLIENTS
     * introduce reqgured parameters
     * inherit required methodsm including all specific API methods

    Important client peculiarities
    ------------------------------
    1. * Acessing by cloud_key (client ID) *
       Google Drive, OneDrive allows full access for any item by IP and for all its operations
       DropBox mainly relies on paths, however instead of path for the most requests it is possible to pass ID with
       equal result
       Owncloud, Nextcloud rely strictly on paths, altough IDs are presented. So, to make a safe API call it is
       necessary to construct the whole tree if items (which have keys) and get path by that key

    2. * Listing children. Constructing the full tree of items instead of applying to each folder *
       Owncloud, Nextcloud, Dropbox allow making recursive children_get request. So, it is possible to construct
       the whole tree at the very moment of client initiating
       Google Drive, OneDrive do not allow that (seems because a single item might have a few parents)
       So, it is not possible to optimize performace for snapshots checks for all clients by replacing all snapshot
       children_get response with a single client request. Besides, it might be quite risky since assumes passing in
       context hundreed of thousands (or even millions) items' dict.
       That's why it is decided to make general approach to get children per folder - with only exclusion of
       Owncloud and Nextcloud, since they do not have capabilities for that.
    """
    _name = "clouds.client"
    _inherit = ["mail.activity.mixin", "mail.thread"]
    _description = "Cloud Client"
    _error_client_state = "Client was not initiated. Check logs. Try to re-connect"

    @api.depends("cloud_client")
    def _compute_method_key(self):
        """
        Compute method for icon_class and method_key
        """
        for cclient in self:
            cclient.icon_class = cclient.cloud_client and ICON_CLIENTS.get(cclient.cloud_client) or "fa fa-refresh"
            cclient.method_key = cclient.cloud_client and METHODS_CLIENTS.get(cclient.cloud_client) or "error"

    @api.depends("active")
    def _compute_stopped(self):
        """
        Compute the special field stopped, which is used to show "active" warning without placing "active"
        on form
        """
        for cclient in self:
            cclient.stopped = not cclient.active

    @api.depends("restrict_db_sync")
    def _compute_restrict_db(self):
        """
        Compute method for restrict_db
        """
        db = self.env.cr.dbname
        for cclient in self:
            cclient.restrict_db = db

    def _inverse_root_folder_name(self):
        """
        Inverse method for root_folder_name
        The goal is to remove illegal characters and make unique per parent

        Methods:
         * _remove_illegal_characters of ir.attachment
        """
        for cclient in self:
            name_formal = self.env["ir.attachment"]._remove_illegal_characters(cclient.root_folder_name)
            if name_formal != cclient.root_folder_name:
                cclient.root_folder_name = name_formal

    name = fields.Char(string="Name", required=True, tracking=1)
    cloud_client = fields.Selection([], string="Cloud client", required=False, tracking=2)
    method_key = fields.Char(
        string="Method Key",
        help="Introduced to have the same API requests for the same cloud clients (e.g. Nextcloud and ownCloud)",
        compute=_compute_method_key,
        store=True,
    )
    state = fields.Selection(
        [("draft", "Not Confirmed"), ("confirmed", "Confirmed"), ("reconnect", "Reconnected/Paused")],
        default="draft",
        string="State",
        copy=False,
        tracking=3,
    )
    error_state = fields.Char(string="Errors", tracking=4, copy=False)
    root_folder_name = fields.Char(
        string="Root folder name", required=True, default="Odoo", inverse=_inverse_root_folder_name,
    )
    root_folder_key = fields.Char(string="Root folder key", readonly=True, default="", copy=False)
    icon_class = fields.Char(compute=_compute_method_key, store=True)
    active = fields.Boolean(string="Active", default=True, copy=False)
    archive_error_retry = fields.Integer(string="Activation error attempts", default=0)
    stopped = fields.Boolean(string="Stopped", compute=_compute_stopped, store=True)
    sequence = fields.Integer(string="Sequence")
    last_establish = fields.Datetime(
        string="Established Time",
        copy=False,
        help="The technical field for the controller info of which client sync is actively established",
    )
    expiration_datetime = fields.Datetime(string="Expiration Time", default=lambda self: fields.Datetime.now())
    turn_backups = fields.Boolean(
        string="Auto database backups",
        help="Check to generate automatic backups of this database for the current cloud client",
    )
    backup_ids = fields.One2many("clouds.backup.strategy", "client_id", string="Backup Strategies")
    restrict_db_sync = fields.Boolean(string="Restrict Database Sync")
    restrict_db = fields.Char(string="Database to Sync", compute=_compute_restrict_db, store=True, readonly=False)

    _order = "sequence, id"

    def action_establish_sync(self):
        """
        The method to login to a related cloud client

        Methods:
         * _check_state_change
         * _establish_connection

        Extra info:
         * Expected singleton
        """
        self._check_state_change()
        if self.state == "confirmed":
            # Explicitly show that since the initial page might be still open after a login
            raise ValidationError(_("The client has been already confirmed. Please refresh the page"))
        action_id = self._establish_connection()
        return action_id

    def action_reconnnect(self):
        """
        The method to login to a related cloud client

        Methods:
         * _check_state_change

        Extra info:
         * Expected singleton
        """
        self._check_state_change()
        self._reconnect_connection()
        self.state = "reconnect"

    def action_reset(self):
        """
        The method to fully clear all the values

        Methods:
         * _reset_connection

        Extra info:
         * Expected singleton
        """
        if not self.active:
            raise ValidationError(_("The client has been already reset"))
        self._check_state_change(True)
        self._reset_connection()
        action_id = self.sudo().env.ref("cloud_base.clouds_client_action").read()[0]
        action_id["target"] = "main"
        return action_id

    def action_get_formview_action(self):
        """
        The method to open cloud client form view

        Returns:
         * dict

        Extra info:
         * Expected singleton
        """
        action = self.sudo().env.ref("cloud_base.clouds_client_action_form_only").read()[0]
        action.update({"res_id": self.id})
        return action

    def _track_subtype(self, init_values):
        """
        Re-write to add custom events
        """
        if "error_state" in init_values:
            if self.error_state:
                return self.sudo().env.ref("cloud_base.mt_cloud_client_error")
            else:
                return self.sudo().env.ref("cloud_base.mt_cloud_client_success")
        return super(clouds_client, self)._track_subtype(init_values)

    def _check_state_change(self, error_state_check=False):
        """
        The method to make sure the state change operation is possible (so, cron is not running)

        Args:
         * error_state_check - bool whether error in connection should block state change
        """
        Config = self.env["ir.config_parameter"].sudo()
        prev_lock_datetime = Config.get_param("cloud_base_lock_time", "")
        if prev_lock_datetime and fields.Datetime.from_string(prev_lock_datetime) > fields.Datetime.now():
            raise ValidationError(_("At the moment the sync is running. Please wait until it is finished"))
        if self.state != "draft" and error_state_check and self.error_state:
            raise ValidationError(_("The operation is not possible until the connection is fixed"))

    def _establish_connection(self):
        """
        The method to undertake all required actions to establish the connection
        That is the method which should be defined in inherited specific client
        If it is needed, the connection state should be also changed there

        Returns:
         * action dict (might be empty if we can stay on the same form)

        Extra info:
         * We do not wrap in try/except to control loggers for API methods
         * last_establish is used for the case when the same client has a few draft instances
         * Expected singleton
        """
        client_method = "action_{}_establish_connection".format(self.method_key)
        method_to_call = getattr(self, client_method)
        connection_establish = method_to_call()
        self.last_establish = fields.Datetime.now()
        return connection_establish

    def _reconnect_connection(self):
        """
        The method to undertake client-specific actions when reconnecting
        That is the method which should be defined in inherited specific client

        Extra info:
         * Expected singleton
        """
        self.ensure_one()

    def _reset_connection(self):
        """
        The method to undertake while resetting sync

        Extra info:
         * Expected singleton
        """
        rule_ids = self.sudo().with_context(active_test=False).env["sync.model"].search([("client_id", "=", self.id)])
        fol_ids = self.sudo().with_context(active_test=False).env["clouds.folder"].search([("client_id", "=", self.id)])
        rule_ids.write({"own_client_id": False})
        fol_ids.write({"own_client_id": False})
        if self.state == "draft":
            # draft clients should be deleted immediately
            self.sudo().unlink()
        else:
            self.active = False

    def _cloud_log(self, result, log_message, log_type=False, need_commit=False):
        """
        The method to initate running logs

        Args:
         * result - bool - if operation was successful or not
         * log_message - char - string - what has happened with explanations
         * log_type - char - if log has a specific, not result-related level, e.g. "DEBUG"

        Methods:
         * _get_or_create_today_logs of clouds.log
         * _cloud_log of clouds.log

        Extra info:
         * should be either Expected singleton or without client at all
        """
        self = self.sudo()
        if self.ids:
            lclient_name = self.name
            lclient_id = self.id
        else:
            lclient_name = "SYNC"
            lclient_id = "CORE" # IMPORTANT: if renamed: change clouds.log methods (including .js action)
        self.env["clouds.log"]._cloud_log(lclient_name, lclient_id, result, log_message, log_type)
        if need_commit:
            self.env["sync.model"]._cloud_commit()

    def _generate_cloud_client_url(self):
        """
        The method to generate the URL of this cloud client form (used for controllers)

        Returns:
         * char

        Extra info:
         * Expected singleton
        """
        config_action = self.sudo().env.ref("cloud_base.clouds_client_action_form_only")
        url = "/web#id={}&view_type=form&model=clouds.client&action={}".format(
            self.id, config_action and config_action.id or ""
        )
        return url

    def _get_new_expiration(self, delta_seconds):
        """
        The method to define whether the current token is expired

        Args:
         * delta_seconds - int (token duration in seconds)

        Returns:
         * datetime

        Extra info:
         * Expected singleton
        """
        return fields.Datetime.now() + timedelta(seconds=delta_seconds)

    ####################################################################################################################
    ##################################   API methods   #################################################################
    ####################################################################################################################
    @api.model
    def _return_client_context(self):
        """
        The method to return necessary to client context
        IMPORTANT: the method should be trigger only in the cron job. For independent API requests apply
         _return_specific_client_context

        Methods:
         * _return_specific_client_context
         * _return_root_child_ids
         * _check_root_folder

        Returns:
         * dict
           ** cclients - dict of client_id/initiated client-related instance
           ** cclient_items - dict of item_id/dict of children (used at the moment only for Owncloud)
           ** sync_queue_context - always True to indicate we are from the planned
        """
        available_clients = {}
        available_client_items = {}
        all_clients = self.with_context(active_test=False).search([("state", "=", "confirmed")])
        for cclient in all_clients:
            extra_ctx = cclient._return_specific_client_context().get("cclients")
            if not extra_ctx:
                continue
            this_client = extra_ctx.get(cclient.id)
            extra_child_ctx = cclient._return_root_child_ids(this_client)
            if not extra_child_ctx.get(cclient.id):
                continue
            if not cclient._check_root_folder(this_client):
                continue
            available_clients.update(extra_ctx)
            available_client_items.update(extra_child_ctx)
        return {"cclients": available_clients, "cclient_items": available_client_items, "sync_queue_context": True}

    def _return_specific_client_context(self, nologs=False):
        """
        The method to prepare context for a specific client
        Used for stand-alone API requests (not inside queue), e.g. for attachment file_read

        Args:
         * nologs - bool - whether to log results (designed mainly for Google Drive)

        Methods:
         * []_get_client - specific client way to initiatiate linked lib

        Returns:
         * dict of cclients
           ** with key as this client id or empty dict

        Extra info:
         * API requests assumed by that method do *NOT* need list of items
         * We can cannot switch this method to general approach, since while getting client it might be necessary
           to apply certain settings (such as "public urls" settings in owncloud)
         * "single_request" is passed in the context when it is independent stand-alone request (e.g. upload), and
           hence it is better to avoid writing in client (for performance and to avoid concurrent updates)
         * Expected singleton
        """
        if self.restrict_db_sync and self.restrict_db != self.env.cr.dbname:
            self._cloud_log(False, "The client sync is restricted by the database name")
            return {"cclients": {}}

        single_request = self._context.get("single_request")
        client_method = "_{}_get_client".format(self.method_key)
        method_to_call = getattr(self, client_method)
        try:
            api_client, cl_log_message = method_to_call()
            if api_client:
                this_client_ctx_key = {self.id: api_client}
                log_message = "The client was successfully initiated"
                if not single_request and self.error_state != False:
                    self.error_state = False
            else:
                this_client_ctx_key = {}
                log_message = "The client wasn't initiated. Try to reconnect. Extra details: {}".format(cl_log_message)
                if not single_request and self.error_state != log_message:
                    self.error_state = log_message
        except Exception as er:
            this_client_ctx_key = {}
            log_message = "The client wasn't initiated. Try to reconnect. Reason: {}".format(er)
            if not single_request and self.error_state != log_message:
                self.error_state = log_message
        if not nologs:
            self._cloud_log(this_client_ctx_key and True or False, log_message)
        return {"cclients": this_client_ctx_key}

    def _return_root_child_ids(self, client_id):
        """
        The method to return the list of all current items within the root folder
        IMPORTANT: it relates only to certain clients (OwnCloud/Nextcloud actually)
                   otherwise True is returned

        Args:
         * client_id - initiated API lib of a related client

        Returns:
         * dict:
          ** key - id of a current client
          ** dict - of child elements

        Extra info:
         * IMPORTANT NOTE: here client is passed in args, not in context, since context is not yet updated
         * "single_request" is passed in the context when it is independent stand-alone request (e.g. upload), and
           hence it is better to avoid writing in client (for performance and to avoid concurrent updates)
         * Expected singleton
        """
        single_request = self._context.get("single_request")
        client_method = "_{}_return_root_child_ids".format(self.method_key)
        log_message = ""
        if hasattr(self, client_method):
            method_to_call = getattr(self, client_method)
            try:
                citems, log_message = method_to_call(client_id)
                if citems.get(self.id):
                    if not single_request:
                        self.error_state = False
                    self._cloud_log(True, "The client successfully returned the root folder children")
                else:
                    if not single_request:
                        self.error_state = log_message
                    self._cloud_log(False, log_message)
            except Exception as er:
                citems = {}
                log_message = "The client could not return the root folder children. Reason: {}".format(er)
                self._cloud_log(False, log_message)
                if not single_request:
                    self.error_state = log_message
        else:
            citems = {self.id: True}
        return citems

    def _check_root_folder(self, client_id):
        """
        The method to check that previously created root folder exists
        We check root folder only in case of cron initiation to avoid too long per-item upload
        The goal is to avoid eternal errors for all child keys, and to have the second safety layer that the client
        has been initiated
        IMPORTANT: it relates only to certain clients (OneDrive/Google Drive/Dropbox/Amazon S3 actually)
        otherwise True is returned

        Args:
         * client_id - initiated API lib of a related client

        Returns:
         * bool

        Extra info:
         * IMPORTANT: here client is passed in args, not in context, since context is not yet updated
         * Expected singleton
        """
        root_method = "_{}_check_root_folder".format(self.method_key)
        res = True
        if hasattr(self, root_method):
            method_to_call = getattr(self, root_method)
            try:
                res, log_message = method_to_call(client_id)
                if res:
                    self.error_state = False
                    self._cloud_log(True, "The client successfully initiated the root folder")
                else:
                    self.error_state = log_message
                    self._cloud_log(False, log_message)
            except Exception as er:
                res = False
                log_message = "The root folder is not available. Reconnect to create a new one. Details: {}".format(er)
                self._cloud_log(False, log_message)
                self.error_state = log_message
        return res

    @api.model
    def _build_path(self, components):
        """
        The method construct path

        Args:
         * components - list of elements like "Odoo" & "Contacts" or "Odoo/Contacts" & "Agrolait"
         * should_be_closed - bool - True if "/" should be at the end
        """
        path = u"/".join(components)
        path = path.replace("//", "/")
        return path

    def _check_api_error(self, error):
        """
        The method to define error type and proper error text

        Args:
         * error - API error object

        Returns:
         * int
          ** 404 - missing error
          ** 400 - misc unresolved error
        """
        client_method = "_{}_{}".format(self.method_key, "check_api_error")
        method_to_call = getattr(self, client_method)
        error_type = method_to_call(error)
        return error_type

    def _api_get_child_items(self, cloud_key=False):
        """
        The method to retrieve all child elements for a folder - a router method to implement for a specific client

        Args:
         * folder_id - clouds.folder object

        Methods:
         * _check_api_error

        Returns:
         * dict:
          ** folder_ids
          ** attachment_ids
           *** cloud_key - char (cloud key)
           *** name - char
         * None if error
         * False if folder is missing in client
        """
        result = None
        try:
            client_method = "_{}_api_get_child_items".format(self.method_key)
            method_to_call = getattr(self, client_method)
            result = method_to_call(cloud_key=cloud_key)
        except Exception as error:
            error_type = self._check_api_error(error)
            basic_error = "The client could not get children for the folder"
            if error_type == 404:
                # If folder was removed, all its children were removed as well
                result = False
                client_mes = "{} {} due to the missing error. Trying later".format(basic_error, cloud_key)
            else:
                result = None
                client_mes = "{} {}. Reason: {}".format(basic_error, cloud_key, error)
            self._cloud_log(False, client_mes)
        return result

    def _call_api_method(self, method_attr, folder_id, attachment_id, cloud_key, args):
        """
        The method to define proper method name and call it

        Args:
         * method_attr - char
         * folder_id - clouds.folder instance
         * attachment_id - ir.attachment instance
         * cloud_key- char
         * args - dict (see possible keys on clouds.queue)

        Methods:
         * _check_api_error

        Returns:
         * tuple:
           ** result - dict.bool ==> depends on the actual API method
           ** error_type (int)
           ** log_message (char)
        """
        result = error_type = log_message = False
        try:
            client_method = "_{}_{}".format(self.method_key, method_attr)
            method_to_call = getattr(self, client_method)
            result = method_to_call(folder_id, attachment_id, cloud_key, args)
        except Exception as error:
            result = False
            error_type = self._check_api_error(error)
            log_message = error
        return result, error_type, log_message

    def _get_parent_folder_key(self, folder_id):
        """
        The method to retrieve parent folder key

        Args:
         * folder_id - clouds.folder object

        Returns:
         * char

        Extra info:
         * if a parent is not synced to the same client, we consider as a parent the very root folder
        """
        if folder_id.parent_id and folder_id.client_id == folder_id.parent_id.client_id:
            parent_key = folder_id.parent_id.cloud_key
        else:
            parent_key = self.root_folder_key
        return parent_key

    def _retrieve_url(self, attachment_id):
        """
        The method to get the attachment url for cloud client if it is needed by the client
        If it differs from the initial one, also write that new URL

        Args:
         * attachment_id - ir.attachment object

        Extra info:
         * Expected singleton

        Returns:
         * char
        """
        url = attachment_id.url
        if not url:
            return False
        try:
            client_method = "_{}_{}".format(self.method_key, "retrieve_url")
            if hasattr(self, client_method):
                method_to_call = getattr(self, client_method)
                url = method_to_call(attachment_id)
                if url != attachment_id.url:
                    attachment_id.sudo().url = url
        except Exception as er:
            url = attachment_id.url
        return url

    def _make_backup(self, folder_id, subname="manual", filestore=True, manifest=False):
        """
        The method to prepare and sync the backup
         1. Initiate the client
         2. Generate the backup
         3. Send it to the clouds
         4. Save it to Odoo

        Args:
         * clouds folder object
         * subname - string (strategy key)
         * filestore - bool
         * manifest - bool

        Methods:
         * _return_specific_client_context
         * _remove_illegal_characters of ir.attachment
         * _call_api_method
         * _extend_based_on_direct_sync/_extend_based_on_back_sync of clouds.snapshot

        Extra info:
         * Expected singleton
        """
        attachment_id = False
        # 1
        ctx = self._context.copy()
        if "cclients" not in ctx.keys():
            new_ctx = self.sudo()._return_specific_client_context()
            ctx.update(new_ctx)
        self = self.with_context(ctx)
        # 2
        try:
            dump = tempfile.NamedTemporaryFile(suffix=".zip")
            with open(dump.name, "wb+") as dump_temp:
                self._cloud_log(True, "Start executing dump_db", need_commit=True)
                dump_stream = dump_db(self.env.cr.dbname, dump_temp, "zip", filestore, manifest)
                self._cloud_log(True, "Finish executing dump_db", need_commit=True)
            file_name = self.env["ir.attachment"]._remove_illegal_characters(
                "{} {} {}.zip".format(self.env.cr.dbname, fields.Datetime.now(), subname)
            )
            file_size = os.path.getsize(dump.name)
            mimetype = "application/zip"
        except Exception as er:
            self._cloud_log(False, "The client cannot perform auto backup: {}".format(er), need_commit=True)
            return attachment_id
        # 3
        result, error_type, log_message = self.with_context(single_request=True)._call_api_method(
            method_attr="upload_file_content",
            folder_id=folder_id,
            attachment_id=False,
            cloud_key=False,
            args={
                "path": dump.name,
                "file_name": file_name,
                "file_size": file_size,
                "mimetype": mimetype,
            }
        )
        if result:
            # 4
            attachment_id = self.sudo().env["ir.attachment"].create({
                "name": file_name,
                "clouds_folder_id": folder_id.id,
                "mimetype": mimetype,
                "file_size": file_size,
            })
            attachment_id.write(result)
            self._cloud_log(True, "The database auto backup was successfully created", need_commit=True)
            self.env["clouds.snapshot"]._extend_based_on_direct_sync(folder_id, attachment_id, "create")
            self.env["clouds.snapshot"]._extend_based_on_back_sync(folder_id, attachment_id, "create")
            self._cloud_log(True, "The database auto backup was reflected in snapshots", need_commit=True)
        else:
            self._cloud_log(False, "The database auto backup failed. Reason: {}".format(log_message))
        return attachment_id

    def _upload_attachment_from_cloud(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to upload a file from cloud
        IMPORTANT: the method is assumed to be triggered only stand-alone (outside of the cron)

        Methods:
         * _call_api_method

        Returns:
         * binary (base64 decoded) or False

        Extra info:
         * single_request is passed to avoid writing client state on each upload (not only for performance,
           but also to avoid concurrent updates)
        """
        result, error_type, log_message = self.with_context(single_request=True)._call_api_method(
            "upload_attachment_from_cloud", folder_id, attachment_id, cloud_key, args)
        if not result:
            if error_type == 404:
                client_mes = "The attachment {} wasn't retrieved from clouds due to the missing error".format(cloud_key)
                result = False
            else:
                client_mes = "The attachment {} was not retrieved from clouds. Reason: {}".format(
                    cloud_key, log_message
                )
                result = None
            self._cloud_log(result, client_mes)
        return result

    def _setup_sync(self, folder_id, attachment_id, cloud_key, args):
        """
        Wrapper method to real API call for folder creation

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _call_api_method
         * _get_parent_folder_key
         * _cloud_log

        Returns:
         * bool or none: True - success; False - failure, None - awaiting
        """
        parent_key = self._get_parent_folder_key(folder_id)
        if not parent_key:
            # no setup if the parent folder is not yet synced
            return None

        result = False
        args.update({"parent_key": parent_key})
        result, error_type, log_message = self._call_api_method("setup_sync", folder_id, attachment_id, cloud_key, args)
        if result:
            folder_id.write(result)
            client_mes = "The folder {},{} was uploaded to clouds".format(folder_id.name, folder_id.id)
            result = True
        elif error_type == 404:
            client_mes = "The folder {},{} was not uploaded to clouds due to the parent folder missing error".format(
                folder_id.name, folder_id.id
            )
            # its parent is deleted, so we fail this task and wait unti it is re-created
            result = False
        else:
            client_mes = "The folder {},{} was not uploaded to clouds. Reason: {}".format(
                folder_id.name, folder_id.id, log_message)
            result = False
        self._cloud_log(result, client_mes)
        return result

    def _update_folder(self, folder_id, attachment_id, cloud_key, args):
        """
        Wrapper method to real API call for folder update to clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _call_api_method
         * _cloud_log

        Returns:
         * bool or none: True - success; False - failure, None - awaiting
        """
        parent_key = self._get_parent_folder_key(folder_id)
        if not parent_key or not folder_id.cloud_key:
            # no folder move or rename if the parent folder or itself is not synced
            return None

        result = False
        args.update({"parent_key": parent_key})
        result, error_type, log_message = self._call_api_method(
            "update_folder", folder_id, attachment_id, cloud_key, args
        )
        if result:
            client_mes = "The folder {},{} was updated in clouds".format(folder_id.name, folder_id.id)
            folder_id.write(result)
            result = True
        elif error_type == 404:
            client_mes = "The folder {},{} was correctly not updated in clouds due to the missing error".format(
                folder_id.name, folder_id.id
            )
            # we can result in True, since if parent is re-created; this folder would be re-created as well
            # if 404 relates to a folder itself, it means it is deleted
            result = True
        else:
            client_mes = "The folder {},{} was not updated in clouds. Reason: {}".format(
                folder_id.name, folder_id.id, log_message
            )
            result = False
        self._cloud_log(result, client_mes)
        return result

    def _upload_file(self, folder_id, attachment_id, cloud_key, args):
        """
        Wrapper method to real API call for file upload to clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _call_api_method
         * _remove_illegal_characters - to make proper cloud name
         * _extend_based_on_direct_sync of clouds.snapshot
         * _cloud_log

        Returns:
         * bool or none: True - success; False - failure, None - awaiting
        """
        if not folder_id.cloud_key or attachment_id.cloud_key:
            # no upload if attachment folder is not yet synced
            # attachment is not also uplaoded if it has laready cloud_key (move scenario)
            return None

        result = False
        if attachment_id.file_size > 0:
            attach_name = attachment_id._remove_illegal_characters(attachment_id.name, str(attachment_id.id), True)
            args.update({"attach_name": attach_name})
            result, error_type, log_message = self._call_api_method(
                "upload_file", folder_id, attachment_id, cloud_key, args
            )
            if result:
                # we do not write attach_name for performance (not to trigger again direct update) and
                # since that is not critical (its Odoo name may still contain illegal symbols)
                # file delete is not anymore triggered automatically, see @api.autovacuum in ir.attachment
                attachment_id._file_delete_special(attachment_id.store_fname)
                attachment_id.write(result)
                self.env["clouds.snapshot"]._extend_based_on_direct_sync(folder_id, attachment_id, "create")
                cli_mes = "The attachment {},{} was uploaded to clouds".format(
                    attachment_id.name, attachment_id.id
                )
                result = True
            elif error_type == 404:
                # we can result in True, since if parent is re-created; this attachment will be re-created as well
                cli_mes = "The attachment {},{} was correctly not uploaded to clouds due to the missing error".format(
                    attachment_id.name, attachment_id.id
                )
                result = True
            else:
                cli_mes = "The attachment {},{} was not uploaded to clouds. Reason: {}".format(
                    attachment_id.name, attachment_id.id, log_message)
                result = False
            self._cloud_log(result, cli_mes)
        else:
            cli_mes = "The attachment {},{} was not uploaded to clouds since it has an empty size".format(
                attachment_id.name, attachment_id.id
            )
            result = True
            self._cloud_log(result, cli_mes, "WARNING")
        return result

    def _update_file(self, folder_id, attachment_id, cloud_key, args):
        """
        Wrapper method to real API call for file update to clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _remove_illegal_characters - to make proper cloud name
         * _call_api_method
         * _extend_based_on_direct_sync of clouds.snapshot
         * _cloud_log

        Returns:
         * bool or none: True - success; False - failure, None - awaiting
        """
        if not folder_id.cloud_key or not attachment_id.cloud_key:
            # no update if the parent folder is not synced or attachment itself is not yet synced
            return None

        result = False
        attach_name = attachment_id._remove_illegal_characters(attachment_id.name, str(attachment_id.id), True)
        args.update({"attach_name": attach_name})
        result, error_type, log_message = self._call_api_method(
            "update_file", folder_id, attachment_id, cloud_key, args
        )
        if result:
            client_mes = "The attachment {},{} was updated in clouds".format(attachment_id.name, attachment_id.id)
            self.env["clouds.snapshot"]._extend_based_on_direct_sync(folder_id, attachment_id, "write")
            attachment_id.write(result)
            result = True
        elif error_type == 404:
            client_mes = "The attachment {},{} was correctly not updated in clouds due to the missing error".format(
                attachment_id.name, attachment_id.id
            )
            # we can result in True, since if parent is re-created; this attachment would be re-created as well
            # if 404 relates to attachment itself, it means it is deleted
            result = True
        else:
            client_mes = "The attachment {},{} was not updated in clouds. Reason: {}".format(
                attachment_id.name, attachment_id.id, log_message
            )
            result = False
        self._cloud_log(result, client_mes)
        return result

    def _delete_file(self, folder_id, attachment_id, cloud_key, args):
        """
        Wrapper method to real API call for file deletion to clouds
        As a result attachment marked for deletion should be also fully removed from Odoo

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _call_api_method
         * _extend_based_on_direct_sync of clouds.snapshot
         * _cloud_log

        Returns:
         * bool or none: True - success; False - failure, None - awaiting
        """
        if not attachment_id.cloud_key:
            return None

        result = False
        result, error_type, log_message = self._call_api_method(
            "delete_file", folder_id, attachment_id, cloud_key, args
        )
        attach_name = attachment_id.name
        attach_id = attachment_id.id
        if result:
            if not args.get("no_odoo_unlink"):
                self.env["clouds.snapshot"]._extend_based_on_direct_sync(folder_id, attachment_id, "delete")
                attachment_id.unlink()
            client_mes = "The attachment {},{} was successfully deleted in clouds".format(attach_name, attach_id)
            result = True
        elif error_type == 404:
            # in 404 deleted disregarding args, since anyway does not exist in clouds
            # However Google Drive returns the 404 error as "successfull operation"
            # So, we have to keep that attachment even it is missed in clouds
            # for _adapt_attachment_reverse_and_delete we have own 404 error processing then
            if not args.get("no_odoo_unlink"):
                self.env["clouds.snapshot"]._extend_based_on_direct_sync(folder_id, attachment_id, "delete")
                attachment_id.unlink()
            client_mes = "The attachment {},{} was deleted in clouds with a missing warning".format(
                attach_name, attach_id
            )
            result = True
        else:
            client_mes = "The attachment {},{},{} was not deleted in clouds. Reason: {}".format(
                attach_name, attach_id, cloud_key, log_message
            )
            result = False
        self._cloud_log(result, client_mes)
        return result

    def _move_file(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to change attachment parent folder in clouds

        IMPORTANT: the critical assumption is that we run this tasks after all tasks inside previous folder based
        on blocking mechanics. After that operations we make sure that attachment and previous folder state are
        up-to-date

        IMPORTANT here we cover all the viable scenarios:
         * f1 client 1 > f2 client 1: just update item
         * f1 client 1 > f2 client 2: get attachment back and plan uploading
           IMPORTANT: plan (NOT do) uploading, since in case of error, we should NOT try to make a reverse again

         * f1 > f2 > f3, ...: do the last tast since initial folder (f1) is taken from attachment while
           preparing (not from the active snapshot). Thus, preparing tasks would generate all moves f1 > f2; f1 > f3; ..
           During *optimizing queue* we delete all ones except the last
         * f1 > f2 > f1: do nothing, since folder is eventually the same (and such a task should be archived during
           optimizing clouds queue). In such a way, recursive blocking within the same folder would not take place,
           and we can safely leave move tasks as the most prioritized

         * f1 client 1 > f2 no client: get attachment back without uploading
         * f1 no client > f2 client 1/2: just upload to f2. The scenario is covered by checking for cloud_key.
           Actully this scenario is possible only in the varian of f1 (reversed). If such case is detected
           during preparation: previous attachments tasks are archived and upload task is planned

         * f1 (reversed) client 1 > f2 client 1/2: just upload to f2. The point here is the move would wait for
           all attachment-related tasks in f1 (by blocking), and attachment should not have cloud_key finally. So,
           that scenario leads to simple f1 no client > f2 client 1
         * f1 client 1 > f2 (reversed) client 1/2: we do practically the same without excess uploading. After move
           we would have adapt_attachment_reverse planned. Such a task with done _adapt_attachment_reverse_and_delete
           would result in simple True

         * f1 client 1 > f2 (reversed) > f3 During *optimizing queue* we delete all moves except the last +
           we delete adapt_attachment_reverse related to that attachment to avoid getting back for incorrect folder

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _upload_file
         * _update_file
         * _adapt_attachment_reverse_and_delete
         * _create_task of clouds.queue

        Returns:
         * bool
        """
        result = False
        previous_folder_id = attachment_id.sync_cloud_folder_id
        if not previous_folder_id:
            # extreme case which should not happen
            self._cloud_log(False, "The attachment was not moved since it or its previous folder was deleted")
            return False
        # used to make sure we do not upload items to clouds when they are in Odoo
        snapshot_reversed = folder_id and folder_id.snapshot_id.reverse_state == "rearranged"
        # since folder might already do not have an active client
        previous_client_id = attachment_id.sync_client_id
        if previous_folder_id == folder_id:
            result = True
        elif not attachment_id.cloud_key:
            if not snapshot_reversed:
                result = self._upload_file(folder_id, attachment_id, cloud_key, args)
        else:
            if previous_client_id == folder_id.client_id:
                result = self._update_file(folder_id, attachment_id, cloud_key, args)
            else:
                if not previous_client_id or previous_client_id.state != "confirmed" or previous_client_id.error_state:
                    previous_client_id = previous_client_id or self.env["clouds.client"]
                    previous_client_id._cloud_log(False, "The client was not available for the sync moves")
                    return False
                result = previous_client_id._adapt_attachment_reverse_and_delete(
                    previous_folder_id, attachment_id, cloud_key, args
                )
                if result and attachment_id.exists() and folder_id.client_id and not snapshot_reversed:
                    # IMPORANT: we rely upon folder_id.client_id (not self), since for not synced folders, the task has
                    # previous_folder_id.client_id as a client
                    # NOTE: attachment might be deleted because of _adapt_attachment_reverse_and_delete if missing
                    self.env["clouds.queue"]._create_task({
                        "name": "upload_file",
                        "task_type": "direct",
                        "client_id": self.id,
                        "folder_id": folder_id.id,
                        "attachment_id": attachment_id.id,
                        "snapshot_id": folder_id.snapshot_id.id,
                        "sequence": 100,
                    })
        return result

    def _create_subfolder(self, folder_id, attachment_id, cloud_key, args):
        """
        Wrapper method to real API call for creating clouds.folder in Odoo

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _call_api_method
         * _cloud_log

        Returns:
         * bool
        """
        result = False
        existing_folder = self.env["clouds.folder"].search([("cloud_key", "=", cloud_key)], limit=1)
        if not existing_folder:
            result, error_type, log_message = self._call_api_method(
                "create_subfolder", folder_id, attachment_id, cloud_key, args
            )
            if result:
                fo_id = self.env["clouds.folder"].with_context(save_snapshot_state=True).create(result)
                fo_id._order_node_after_dnd(fo_id.parent_id and fo_id.parent_id.id or False, False)
                self.env["clouds.snapshot"]._extend_folders_on_back_sync(fo_id)
                client_mes = "The folder {},{} was created in Odoo based on the cloud data".format(fo_id.name, fo_id.id)
                result = True
            elif error_type == 404:
                client_mes = "The folder {} was correctly not created in Odoo due to the missing error".format(
                    cloud_key
                )
                result = True
            else:
                client_mes = "The folder {} was not created in Odoo based on the cloud data. Reason: {}".format(
                    cloud_key, log_message,
                )
                result = False
        else:
            client_mes = "The folder {} was not created in Odoo. Avoid moving folders in clouds!".format(cloud_key)
            result = True
        self._cloud_log(result, client_mes)
        return result

    def _create_attachment(self, folder_id, attachment_id, cloud_key, args):
        """
        Wrapper method to real API call for creating ir.attachment in Odoo

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _call_api_method
         * _extend_based_on_back_sync of clouds.snapshot
         * _cloud_log

        Returns:
         * bool

        Extra info:
         * we do not check for existing attachment, since assumed that it might be moved in clouds.
           So, we unlink previous Odoo attachment and create a brand new one
        """
        result = False
        result, error_type, log_message = self._call_api_method(
            "create_attachment", folder_id, attachment_id, cloud_key, args
        )
        if result:
            att_id = self.env["ir.attachment"].create(result)
            cli_mes = "The attachment {},{} was created in Odoo based on the cloud data".format(att_id.name, att_id.id)
            self.env["clouds.snapshot"]._extend_based_on_back_sync(folder_id, att_id, "create")
            result = True
        elif error_type == 404:
            cli_mes = "The attachment {} was correctly not created in Odoo from clouds due to the missing error".format(
                cloud_key
            )
            result = True
        else:
            cli_mes = "The attachment {} was not created in Odoo based on the cloud data. Reason: {}".format(
                cloud_key, log_message,
            )
            result = False
        self._cloud_log(result, cli_mes)
        return result

    def _change_attachment(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to updated attachment based on previously received task from clouds
        Does NOT assume API request

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _call_api_method
         * _extend_based_on_back_sync of clouds.snapshot
         * _cloud_log

        Returns:
         * bool - always True, since all conditions lead to the same result
        """
        result = False
        att_id = self.env["ir.attachment"].search(
            [("cloud_key", "=", cloud_key), ("clouds_folder_id", "=", folder_id.id)], limit=1
        )
        if att_id:
            result, error_type, log_message = self._call_api_method(
                "change_attachment", folder_id, attachment_id, cloud_key, args
            )
            if result:
                att_id.write(result)
                cli_mes = "The attachment {},{} was updated in Odoo based on the cloud data".format(
                    att_id.name, att_id.id
                )
                self.env["clouds.snapshot"]._extend_based_on_back_sync(folder_id, att_id, "write")
                result = True
            elif error_type == 404:
                cli_mes = "The attachment {},{} was correctly not updated from clouds due to the missing error".format(
                    att_id.name, att_id.id
                )
                result = True
            else:
                cli_mes = "The attachment {} was not updated in Odoo based on the cloud data. Reason: {}".format(
                    cloud_key, log_message,
                )
                result = False
        else:
            cli_mes = "The attachment {} was not updated in Odoo since it has been already deleted".format(cloud_key)
            result = True
        self._cloud_log(result, cli_mes)
        return result

    def _unlink_attachment(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to delete attachment based on previously received task from clouds
        Does NOT assume API request

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _extend_based_on_back_sync of clouds.snapshot
         * _cloud_log

        Returns:
         * bool - always True, since all conditions lead to the same result

        Extra info:
         * We leave all conditions for transperance reason (an for the case of code evolvement)
         * we search inside the current folder to avoid client moving scenario, when an a new attachment is created in
           Odoo
         * if attachment is not found, it is positive scenario (most probably means attachment was manually deleted in
           Odoo)
         * we write "for_delete", since attachment should be fully removed
        """
        result = False
        att_id = self.env["ir.attachment"].search(
            [("cloud_key", "=", cloud_key), ("clouds_folder_id", "=", folder_id.id)], limit=1
        )
        if att_id:
            cli_mes = "The attachment {},{} was deleted in Odoo based on the cloud data".format(att_id.name, att_id.id)
            att_id.write({"for_delete": True})
            self.env["clouds.snapshot"]._extend_based_on_back_sync(folder_id, att_id, "delete")
            att_id.unlink()
            result = True
        else:
            cli_mes = "The attachment {} was not deleted in Odoo since it has been already deleted".format(cloud_key)
            result = True
        self._cloud_log(result, cli_mes)
        return result

    def _create_subfolder_reverse(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create subfolder in Odoo based on cloud data during reverse sync
        This folder is assumed to bre recursively synced again, since its content should be in Odoo after that
        So it is put in Odoo, adapted to trigger reverse tasks, awaits for new tasks created, and awaits to be deleted
        from clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _call_api_method
         * _cloud_log

        Returns:
         * bool
        """
        existing_folder = self.env["clouds.folder"].search([("cloud_key", "=", cloud_key)], limit=1)
        if not existing_folder:
            result, error_type, log_message = self._call_api_method(
                "create_subfolder", folder_id, attachment_id, cloud_key, args
            )
            if result:
                fo_id = self.env["clouds.folder"].with_context(save_snapshot_state=True).create(result)
                # need to make sure its children would be recusrively updatied until finalizing
                self.env["clouds.snapshot"]._adapt_for_reverse_creation(fo_id, args)
                cli_mes = "The folder {},{} was created (reverse) in Odoo based on the cloud data".format(
                    fo_id.name, fo_id.id
                )
                result = True
            elif error_type == 404:
                cli_mes = "The folder {} was not created (reverse) in Odoo due to the missing error".format(
                    cloud_key
                )
                result = True
            else:
                cli_mes = "The folder {} was not created (reverse) in Odoo based on the cloud data. Reason: {}".format(
                    cloud_key, log_message,
                )
                result = False
        else:
            cli_mes = "The folder {} wasn't created (reverse) in Odoo. Avoid moving folders in clouds".format(cloud_key)
            result = True
        self._cloud_log(result, cli_mes)
        return result

    def _create_attachment_reverse(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create attachment in Odoo based on cloud data as it is not synced at all

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _call_api_method
         * _cloud_log

        Returns:
         * bool

        Extra info:
         * deletion would be done once when the very root folder is removed
        """
        result, error_type, log_message = self._call_api_method(
            "attachment_reverse", folder_id, attachment_id, cloud_key, args
        )
        if result:
            if not result.get("clouds_folder_id"):
                result.update({"clouds_folder_id": folder_id and folder_id.id or False})
            att_id = self.env["ir.attachment"].create(result)
            cli_mes = "The attachment {},{} was created (reverse) in Odoo based on the cloud data".format(
                att_id.name, att_id.id
            )
            result = True
        elif error_type == 404:
            cli_mes = "The attachment {} was not created (reverse) in Odoo due to the missing error".format(
                cloud_key
            )
            result = True
        else:
            cli_mes = "The attachment {} wasn't created (reverse) in Odoo based on the cloud data. Reason: {}".format(
                cloud_key, log_message,
            )
            result = False
        self._cloud_log(result, cli_mes)
        return result

    def _delete_file_reverse(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to fully remove attachment in Odoo because of direct sync task

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Returns:
         * bool

        Extra info:
         * deletion would be done once when the very root folder is removed
        """
        attachment_id.unlink()
        return True

    def _adapt_attachment_reverse(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to write attachment in Odoo with binary based on cloud data. Attachment is not anymore considered
        as synced

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _call_api_method
         * _cloud_log

        Returns:
         * bool

        Extra info:
         * deletion would be done once when the very root folder is removed
        """
        if not attachment_id.cloud_key:
            # the queue might include attachments which have not synced, so nothing should be done
            return True
        result, error_type, log_message = self._call_api_method(
            "attachment_reverse", folder_id, attachment_id, attachment_id.cloud_key, args
        )
        if result:
            attachment_id.write(result)
            client_mes = "The attachment {},{} was reversed in Odoo based on the cloud data".format(
                attachment_id.name, attachment_id.id
            )
            result = True
        elif error_type == 404:
            client_mes = "The attachment {},{} was not reversed in Odoo since it is missing. So, it was deleted".format(
                attachment_id.name, attachment_id.id
            )
            # to avoid "hanging" synced files without real content, here we also unlink such an attachment
            attachment_id.write({"for_delete": True})
            attachment_id.unlink()
            # no sense to keep a task, since a linked file was deleted
            result = True
        else:
            client_mes = "The attachment {},{} was not reversed in Odoo based on the cloud data. Reason: {}".format(
                attachment_id.name, attachment_id.id, log_message,
            )
            result = False
        self._cloud_log(result, client_mes)
        return result

    def _adapt_attachment_reverse_and_delete(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to write attachment in Odoo with binary based on cloud data. Attachment is not anymore considered
        as synced. In clouds it should be deleted since after that it would re-created with a new task

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _call_api_method
         * _delete_file
         * _cloud_log

        Returns:
         * bool

        Extra info:
         * deletion would be done once when the very root folder is removed
         * no check for 404 error of _delete_file, since some client (Google Drive!) responds with that as success
        """
        if not attachment_id.cloud_key:
            # the queue might include attachments which have not synced, so nothing should be done
            return True
        result, error_type, log_message = self._call_api_method(
            "attachment_reverse", folder_id, attachment_id, attachment_id.cloud_key, args
        )
        if result:
            deletion_result = self._delete_file(folder_id, attachment_id, attachment_id.cloud_key, args)
            if deletion_result:
                attachment_id.write(result)
                cli_mes = "The attachment {},{} was reversed to Odoo since it had been moved".format(
                    attachment_id.name, attachment_id.id
                )
                result = True
            else:
                # _delete_file returns False / None only in case of serious issues
                cli_mes = "The attachment {},{} was not reversed due to an unexpected error. Check logs".format(
                    attachment_id.name, attachment_id.id
                )
                result = False
        elif error_type == 404:
            cli_mes = "The attachment {} was correctly not reversed to Odoo (moving) due to the missing error".format(
                cloud_key
            )
            # to avoid "hanging" synced files without real content, here we also unlink such an attachment
            attachment_id.write({"for_delete": True})
            attachment_id.unlink()
            result = True
        else:
            cli_mes = "The attachment {} was not updated in Odoo (moving) based on the cloud data. Reason: {}".format(
                cloud_key, log_message,
            )
            result = False
        self._cloud_log(result, cli_mes)
        return result

    def _adapt_folder_reverse(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to write folder in Odoo as it is not any more synced

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * _call_api_method
         * _cloud_log

        Returns:
         * bool
        """
        def _update_folder():
            """
            The method to finish inlinking of this and child folders
            """
            incl_child_folder_ids = self.env["clouds.folder"].with_context(active_test=False).search(
                [("id", "child_of", folder_id.id)]
            )
            incl_child_folder_ids.write({"cloud_key": False, "url": False})
            snapshot_id = folder_id.snapshot_id
            incl_child_snapshot_ids = self.env["clouds.snapshot"].with_context(active_test=False).search([
                ("id", "child_of", snapshot_id.id)
            ])
            incl_child_snapshot_ids.write({"reverse_state": "normal", "reverse_client_id": False})

        if not folder_id.cloud_key:
            # folder is already inlinked (e.g. during a parent folder unlink). So, task is just marked done
            _update_folder()
            return True

        result, error_type, log_message = self._call_api_method(
            "delete_folder", folder_id, attachment_id, folder_id.cloud_key, args
        )
        if result:
            _update_folder()
            client_mes = "The folder {},{} has finished the reversed sync to Odoo".format(folder_id.name, folder_id.id)
            result = True
        elif error_type == 404:
            _update_folder()
            client_mes = "The folder {},{} has finished the reversed sync to Odoo with a missing warning".format(
                folder_id.name, folder_id.id
            )
            result = True
        else:
            client_mes = "The folder {},{} has not finished the reversed sync to Odoo. Reason: {}".format(
                folder_id.name, folder_id.id, log_message,
            )
            result = False
        self._cloud_log(result, client_mes)
        return result
