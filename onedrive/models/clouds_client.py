# -*- coding: utf-8 -*-

import json
import os
import re

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

from ..libs.onedrive_service import OnedriveApiClient as Client

# "openid" - to able to sign (under consideration whether it is really requried)
# "Files.ReadWrite.All" - read and write in all files
# "offline_access" - to receive refresh_token instead of one-hour durable
SCOPES = ["openid", "Files.ReadWrite.All", "offline_access"]


class clouds_client(models.Model):
    """
    Overwrite to add google drive methods
    """
    _inherit = "clouds.client"

    def _default_onedrive_redirect_uri(self):
        """
        The method to return default for onedrive_redirect_uri
        """
        Config = self.env["ir.config_parameter"].sudo()
        base_odoo_url = Config.get_param("web.base.url", "http://localhost:8069")
        return "{}/one_drive_token".format(base_odoo_url)

    cloud_client = fields.Selection(
        selection_add=[("onedrive", "OneDrive"), ("sharepoint", "SharePoint")],
        required=True,
        ondelete={"onedrive": "cascade", "sharepoint": "cascade"},
        default="onedrive",
    )
    onedrive_client_id = fields.Char(string="OneDrive/SharePoint app client ID")
    onedrive_client_secret = fields.Char(string="OneDrive/SharePoint app secret key")
    onedrive_redirect_uri = fields.Char(
        string="OneDrive/SharePoint redirect URL",
        default=_default_onedrive_redirect_uri,
        help="The same redirect URL should be applied to your Microsoft app settings",
    )
    onedrive_sharepoint_base_url = fields.Char(
        string="SharePoint URL",
        help="The SharePoint URL should have the form https://[URL]/: the last '/' is required. The site name should\
not be included in the URL",
    )
    onedrive_sharepoint_site_name = fields.Char(
        string="SharePoint site",
        help="""The SharePoint site should be either 'my_site_name' (in that case it is considered\
'sites/my_site_name') or 'sites/my_site_name'. Instead of 'sites', it might be 'teams', for example. There should be no\
'/' at the beginning or at the end. Use 'root' to apply the SharePoint root site"""
    )
    onedrive_sharepoint_drive = fields.Char(
        string="Documents Library",
        help="In SharePoint, you might have a few document libraries (drives). The standard one is 'Documents', but you\
create as many as you want. Within this document library, the root sync folder will be generated",
        default="Documents",
    )
    onedrive_session = fields.Char(string="OneDrive/SharePoint active token", readonly=True, default="")
    onedrive_key = fields.Char(string="OneDrive/SharePoint library key", readonly=True, default="")

    def action_onedrive_establish_connection(self):
        """
        The method to establish connection for OneDrive/SharePoint

        Methods:
         * _od_get_auth_url

        Returns:
         * action window to confirm in google

        Extra info:
         * Expected singleton
        """
        auth_url = self._od_get_auth_url()
        res = {"name": "Microsoft App", "type": "ir.actions.act_url", "url": auth_url}
        return res

    ####################################################################################################################
    ##################################   LOG IN METHODS ################################################################
    ####################################################################################################################
    def _od_get_auth_url(self):
        """
        Get URL of authentification page
         1. Clean session, if new url is required

        Methods:
         * _onedrive_get_client
         * authorization_url of Microsoft Api Client

        Returns:
         * char - url of application to log in

        Extra info:
         * Expected singleton
        """
        self.write({"onedrive_session": "", "expiration_datetime": fields.Datetime.now()}) # 1
        self._cloud_log(True, "The app confirmation process was started", "DEBUG")
        odrive_client, log_message = self._onedrive_get_client(new_token_required=True)
        if odrive_client:
            self.error_state = False
            res = odrive_client.authorization_url(self.onedrive_redirect_uri, SCOPES, state=None)
        else:
            self.error_state = log_message
            res = self.sudo().env.ref("cloud_base.clouds_client_action_form_only").read()[0]
            res["res_id"] = self.id
        return res

    def _od_create_session(self, code=False):
        """
        Authenticates to OneDrive/SharePoint

        Args:
         * code - authorization code received

        Methods:
         * exchange_code of Microsoft Api Client
         * set_token
         * refresh_token of Microsoft Api Client
         * _onedrive_root_directory
         * _cloud_log

        Returns:
         * tuple
          ** bool - True if authentication is done, False otherwise
          ** char - log_message

        Extra info:
         * The structure of tokens/codes is: authorization_code > refresh_token > access_token
         * Expected singleton
        """
        result = log_message = True
        api_client = self._context.get("cclients", {}).get(self.id)
        if code:
            token = api_client.exchange_code(redirect_uri=self.onedrive_redirect_uri, code=code)
            if not token:
                log_message = "It is not possible to authenticate: check credentials!"
                result = False
            else:
                self.write({"onedrive_session": token, "expiration_datetime": fields.Datetime.now()})
                refresh_token = api_client.refresh_token(
                    redirect_uri=self.onedrive_redirect_uri, refresh_token=token.get("refresh_token"),
                )
                api_client.set_token(refresh_token)
                log_message = "Token was received"
                result = True
        else:
            log_message = "It is not possible to authenticate: make sure you have granted all permissions"
            result = False
        self._cloud_log(result, log_message)
        return result, log_message

    def _od_search_drive_id(self):
        """
        Method to find drive_id in OneDrive/SharePoint of selected directory if it is a team drive or user drive instead

        Methods:
         * _od_get_site_id
         * drives_list_o of Microsoft Api Client
         * personal_drive_o of Microsoft Api Client
         * _cloud_log

        Returns:
         * tuple
          ** bool - True if authentication is done, False otherwise
          ** char - log_message
        """
        result = log_message = True
        api_client = self._context.get("cclients", {}).get(self.id)
        if self.cloud_client == "sharepoint":
            drive_name = self.onedrive_sharepoint_drive
            try:
                site_id = self._od_get_site_id(api_client=api_client)
                drives = api_client.drives_list_o(site_id=site_id)
                self._cloud_log(True, "SharePoint found drives response: {}".format(drives), "DEBUG")
                for prop in drives["value"]:
                    if prop["name"] == drive_name:
                        self.onedrive_key = prop["id"]
                        result = True
                        log_message = "SharePoint library was successfully found"
                        break
                else:
                    result = False
                    log_message = """The SharePoint library wasn't found.
Make sure that the library with the name {} actually exists on the specified site.
Make sure there are no extra symbols or spaces in the drive name.
Check that your user is a full-rights admin who might list drives""".format(drive_name)
            except Exception as error:
                result = False
                log_message = """The SharePoint library wasn't found.
Make sure that the library with the name {} actually exists on the specified site.
Make sure there are no extra symbols or spaces in the drive name.
Check that your user is a full-rights admin who might list drives.
Error: {}""".format(drive_name, error)
        else:
            # if it is not SharePoint, then there is a single drive only
            try:
                personal_drive = api_client.personal_drive_o()
                self.onedrive_key = personal_drive.get("id")
                result = True
                log_message = "The OneDrive library was successfully found"
            except Exception as error:
                result = False
                log_message = "The personal drive wasn't found. Check that your user is a full-rights admin.\
Error: {}".format(error)
        self._cloud_log(result, log_message)
        return result, log_message

    @api.model
    def _od_get_site_id(self, api_client):
        """
        The method to return sharepoint site id based on url and site name

        Args:
         * api_client - instance of Microsoft Api Client

        Methods:
         *  sharepoint_site_o of Microsoft Api Client

        Returns:
         * char
        """
        site_name = self.onedrive_sharepoint_site_name
        relative_path = "root"
        if site_name != "root":
            base_url = self.onedrive_sharepoint_base_url
            # Need to replace extra params and the closing dash
            base_url = base_url.replace("http://","")
            base_url = base_url.replace("https://","")
            base_url = re.sub(r'(www.)(?!com)',r'',base_url)
            if base_url[-1] == "/":
                base_url = base_url[:len(base_url)-1]
            if site_name.find("/") == -1:
                site_name = "sites/{}".format(site_name)
            relative_path = "{}:/{}".format(base_url, site_name)
        site = api_client.sharepoint_site_o(path=relative_path)
        site_id = site.get("id")
        return site_id

    def _od_root_folder_wrapper(self,):
        """
        The method to make initial setup of the root folder

        Methods:
         * _onedrive_root_directory

        Returns:
         * tuple
          ** bool - True if authentication is done, False otherwise
          ** char - log_message
        """
        root_dir = self._onedrive_root_directory()
        if root_dir:
            self.write({"state": "confirmed"})
            log_message = "Authentication was successfully done"
            result = True
        else:
            log_message = "Could not authenticate: root folder cannot be created. Check logs"
            result = False
        self._cloud_log(result, log_message)
        return result, log_message

    ####################################################################################################################
    ##################################   API methods   #################################################################
    ####################################################################################################################
    def _onedrive_get_client(self, new_token_required=False):
        """
        Method to return instance of OneDrive/SharePoint API Client

        Args:
         * new_token_required - bool - whether we can retrieve a token from existng auth code

        Methods:
         * get_token_from_refresh_token of Microsoft Api Client
         * _get_new_expiration
         * _cloud_log

        Returns:
         * tuple:
          ** GoogleDrive instance if initiated. False otherwise
          ** char

        Extra info:
         * Expected singleton
        """
        log_message = ""
        api_client = False
        try:
            if self.onedrive_session and not new_token_required:
                self._cloud_log(True, "Process of initiating client was started", "DEBUG")
            api_client = Client(self.onedrive_client_id, self.onedrive_client_secret, cloud_client=self)
            if self.onedrive_session and not new_token_required:
                new_refresh_token_needed = False
                if self.expiration_datetime > fields.Datetime.now():
                    try:
                        refresh_token = json.loads(self.onedrive_session)
                        api_client.set_token(refresh_token)
                        log_message = "Using previous token"
                        self._cloud_log(True, log_message, "DEBUG")
                    except:
                        new_refresh_token_needed = True
                else:
                    new_refresh_token_needed = True
                if new_refresh_token_needed:
                    refresh_token = api_client.refresh_token(
                        redirect_uri=self.onedrive_redirect_uri,
                        refresh_token=safe_eval(self.onedrive_session).get("refresh_token"),
                    )
                    self.write({
                        "onedrive_session": json.dumps(refresh_token),
                        "expiration_datetime": self._get_new_expiration(2699), # token life = 60min - 15min for cron
                    })
                    api_client.set_token(refresh_token)
                    log_message = "Got token from refresh token"
                    self._cloud_log(True, log_message, "DEBUG")
        except Exception as er:
            api_client = False
            log_message = "Could not authenticate. Reason: {}".format(er)
            self._cloud_log(False, log_message)
        return api_client, log_message

    def _onedrive_check_root_folder(self, client_id):
        """
        The method to check whether the root folder exists

        Args:
         * client_id - instance of Microsoft Api Client

        Methods:
         * get_drive_item_o of Microsoft Api Client

        Returns:
         * True

        Extra info:
         * IMPORTANT NOTE: here client is passed in args, not in context, since context is not yet updated
         * Expected singleton
        """
        log_message = ""
        res = True
        odoo_path = client_id.get_drive_item_o(drive_id=self.onedrive_key, drive_item_id=self.root_folder_key)
        if not odoo_path:
            res = False
            child_items = {}
            log_message = "The root folder is not available. Reconnect to create a new one"
        return res, log_message

    def _onedrive_check_api_error(self, error):
        """
        The method to get an error type based on response

        Args:
         * error class related to API

        Retunes:
         * int
        """
        error_type = 400
        if type(error).__name__ == "NotFound":
            error_type = 404
        return error_type

    def _onedrive_root_directory(self):
        """
        Method to return root directory name and id (create if not yet)

        Methods:
         * _check_api_error
         * get_drive_item_o of Microsoft Api Client
         * create_folder_o of Microsoft Api Client
         * _cloud_log

        Returns:
         * key, name - name of folder and key in client
         * False, False if failed
        """
        client = self._context.get("cclients", {}).get(self.id)
        res_id = self.root_folder_key
        res = False
        if res_id:
            try:
                #in try, since the folder might be removed in meanwhile
                res = client.get_drive_item_o(drive_id=self.onedrive_key, drive_item_id=res_id)
                self._cloud_log(True, "The root directory {},{} was successfully found".format(
                    self.root_folder_name, self.root_folder_key
                ))
            except Exception as error:
                if self._check_api_error(error) == 404:
                    res_id = False # to guarantee creation of item
                    self._cloud_log(
                        False,
                        "The root directory {}{} was removed from the clouds. Creating a new one".format(
                            self.root_folder_name, self.root_folder_key
                        ),
                        "WARNING",
                    )
                else:
                    self._cloud_log(False, "Unexpected error while searching the root directory {},{}: {}".format(
                        self.root_folder_name, self.root_folder_key, error
                    ))
                    res_id = True # to guarantee no creation of item
                    res = False
        if not res_id:
            try:
                res_id = client.create_folder_o(
                    drive_id=self.onedrive_key, folder_name=self.root_folder_name, parent="root",
                ).get("id")
                self.root_folder_key = res_id
                self._cloud_log(True, "The root directory {} was successfully created".format(self.root_folder_name))
                res = res_id
            except Exception as error:
                res = False
                self._cloud_log(
                    False,
                    "Unexpected error during the root directory {} creation: {}".format(self.root_folder_name, error)
                )
        return res and True or False

    def _onedrive_api_get_child_items(self, cloud_key=False):
        """
        The method to retrieve all child elements for a folder
        Note: If folder was removed, all its children were removed as well

        Args:
         * cloud_key - char

        Methods:
         * children_items_o of Microsoft Api Client

        Returns:
         * dicts:
          ** folder_ids
          ** attachment_ids
           *** cloud_key - char (cloud key)
           *** name - char
        """
        client = self._context.get("cclients", {}).get(self.id)
        items = client.children_items_o(drive_id=self.onedrive_key, drive_item_id=cloud_key)
        attachments = []
        subfolders = []
        for child in items:
            res_vals = {"cloud_key": child.get("id"),"name": child.get("name"),}
            if child.get("folder"):
                subfolders.append(res_vals)
            else:
                attachments.append(res_vals)
        return {"folder_ids": subfolders, "attachment_ids": attachments}

    def _onedrive_retrieve_url(self, attachment_id):
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
        client = self.sudo()._return_specific_client_context().get("cclients", {}).get(self.id)
        cdata = client.get_drive_item_o(drive_id=self.onedrive_key, drive_item_id=attachment_id.cloud_key)
        return cdata.get("webUrl") or attachment_id.url

    def _onedrive_upload_attachment_from_cloud(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to upload a file from cloud

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * download_file_o of Microsoft Api Client

        Returns:
         * binary (base64 decoded)
         * False if method failed
        """
        client = self._context.get("cclients", {}).get(self.id)
        result = client.download_file_o(drive_id=self.onedrive_key, drive_item=attachment_id.cloud_key)
        return result

    def _onedrive_setup_sync(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create folder in clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)
         * args should contain "parent_key"

        Methods:
         * create_folder_o of Microsoft Api Client

        Returns:
         * dict of values to write in clouds.folder

        Extra info:
         * setup sync assumes that a folder does not exist in client. If a folder was previously deactivated,
           it was just deleted from clouds
        """
        result =  False
        client = self._context.get("cclients", {}).get(self.id)
        result = client.create_folder_o(
            drive_id=self.onedrive_key, folder_name=folder_id.name, parent=args.get("parent_key"),
        )
        result = {"cloud_key": result.get("id"), "url": result.get("webUrl")}
        return result

    def _onedrive_update_folder(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to update folder in clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)
         * in args we should receive parent_key

        Methods:
         * move_or_update_item_o of Microsoft Api Client

        Returns:
         * dict of values to write in clouds folder
        """
        client = self._context.get("cclients", {}).get(self.id)
        result = client.move_or_update_item_o(
            drive_id=self.onedrive_key,
            drive_item_id=folder_id.cloud_key,
            new_parent=args.get("parent_key"),
            new_name=folder_id.name,
        )
        result = {"cloud_key": result.get("id"), "url": result.get("webUrl")}
        return result

    def _onedrive_delete_folder(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to delete folder in clouds
        The method is triggered directly from _adapt_folder_reverse (cloud_client does not have _delete_folder)
        UNDER NO CIRCUMSTANCES DO NOT DELETE THIS METHOD

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * delete_file_o of Microsoft Api Client

        Returns:
          * bool

        Extra info:
         * Actually the result of the operation is always an error. 204 if successful, so, return would never take place
        """
        result = False
        client = self._context.get("cclients", {}).get(self.id)
        result = client.delete_file_o(drive_id=self.onedrive_key, drive_item_id=folder_id.cloud_key,)
        return result and True and False

    def _onedrive_upload_file(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to upload file to clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)
         * args should contain attach_name

        Methods:
         * upload_large_file_o of Microsoft Api Client

        Returns:
         * dict of values to write in ir.attachment

        Extra info:
         * we do not check for uniqueness of attachment name, since OneDrive would do that for us
        """
        client = self._context.get("cclients", {}).get(self.id)
        file_path = attachment_id._full_path(attachment_id.store_fname)
        result = client.upload_large_file_o(
            drive_id=self.onedrive_key,
            folder_name=folder_id.cloud_key,
            file_name=args.get("attach_name"),
            path=file_path,
            file_size=os.path.getsize(file_path),
        )
        result = {
            "cloud_key": result.get("id"),
            "url": result.get("webUrl"),
            "type": "url",
            "sync_cloud_folder_id": folder_id.id,
            "sync_client_id": self.id,
        }
        return result

    def _onedrive_upload_file_content(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to send binary content to clouds
        """
        client = self._context.get("cclients", {}).get(self.id)
        result = client.upload_large_file_o(
            drive_id=self.onedrive_key,
            folder_name=folder_id.cloud_key,
            file_name=args.get("file_name"),
            path=args.get("path"),
            file_size=args.get("file_size"),
        )
        result = {
            "cloud_key": result.get("id"),
            "url": result.get("webUrl"),
            "type": "url",
            "sync_cloud_folder_id": folder_id.id,
            "sync_client_id": self.id,
        }
        return result

    def _onedrive_update_file(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to update file in clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)
         * Args should contain attach_name

        Methods:
         * move_or_update_item_o of Microsoft Api Client

        Returns:
         * dict to write in attachment

        Extra info:
         * we do not check for uniqueness of attachment name, since Gogole Drive would do that for us
        """
        client = self._context.get("cclients", {}).get(self.id)
        result = client.move_or_update_item_o(
            drive_id=self.onedrive_key,
            drive_item_id=attachment_id.cloud_key,
            new_parent=folder_id.cloud_key,
            new_name=args.get("attach_name"),
        )
        result = {
            "cloud_key": result.get("id"),
            "url": result.get("webUrl"),
            "sync_cloud_folder_id": folder_id.id,
            "sync_client_id": self.id,
        }
        return result

    def _onedrive_delete_file(self, folder_id, attachment_id, cloud_key, args):
        """
        Method to delete file in clouds

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * delete_file_o of Microsoft Api Client

        Returns:
          * bool

        Extra info:
         * Actually the result of the operation is always an error. 204 if successful, so, return would never take place
        """
        result = False
        client = self._context.get("cclients", {}).get(self.id)
        result = client.delete_file_o(drive_id=self.onedrive_key, drive_item_id=attachment_id.cloud_key)
        return result and True or False

    def _onedrive_create_subfolder(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create clouds.folder in Odoo based on cloud client folder info

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * get_drive_item_o of Microsoft Api Client

        Returns:
          * dict of clouds.folder values
        """
        client = self._context.get("cclients", {}).get(self.id)
        cdata = client.get_drive_item_o(drive_id=self.onedrive_key, drive_item_id=cloud_key)
        result = {
            "cloud_key": cloud_key,
            "name": cdata.get("name"),
            "parent_id": folder_id.id,
            "own_client_id": self.id,
            "active": True,
            "url": cdata.get("webUrl"),
        }
        return result

    def _onedrive_create_attachment(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create ir.attachment in Odoo based on cloud client file info

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * get_drive_item_o of Microsoft Api Client

        Returns:
          * dict of ir.attachment values
        """
        client = self._context.get("cclients", {}).get(self.id)
        cdata = client.get_drive_item_o(drive_id=self.onedrive_key, drive_item_id=cloud_key)
        result = {
            "cloud_key": cloud_key,
            "name": cdata.get("name"),
            "url": cdata.get("webUrl"),
            "clouds_folder_id": folder_id.id,
            "sync_cloud_folder_id": folder_id.id,
            "sync_client_id": self.id,
            "type": "url",
            "mimetype": cdata.get("file") and cdata.get("file").get("mimeType") or None,
        }
        return result

    def _onedrive_change_attachment(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to write on ir.attachment in Odoo based on cloud client file info

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * get_drive_item_o of Microsoft Api Client

        Returns:
          * dict of ir.attachment values
        """
        client = self._context.get("cclients", {}).get(self.id)
        cdata = client.get_drive_item_o(drive_id=self.onedrive_key, drive_item_id=cloud_key)
        result = {"name": cdata.get("name"), "url": cdata.get("webUrl")}
        return result

    def _onedrive_attachment_reverse(self, folder_id, attachment_id, cloud_key, args):
        """
        The method to create ir.attachment in Odoo based on cloud client file info

        Args:
         * the same as for _call_api_method of clouds.client (cloud.base)

        Methods:
         * get_drive_item_o of Microsoft Api Client
         * download_file_o of Microsoft Api Client

        Returns:
          * dict of ir.attachment values

        Extra info:
         * IMPORTANT: mimetype should NOT be written here, since we already do that in backward sync creation.
           Otherwise, there might be conflicts
        """
        client = self._context.get("cclients", {}).get(self.id)
        cdata = client.get_drive_item_o(drive_id=self.onedrive_key, drive_item_id=cloud_key)
        # IMPORTANT: do not write clouds_folder_id. It would break attachments moves
        result = {
            "cloud_key": False,
            "name": cdata.get("name"),
            "url": False,
            "type": "binary",
            "sync_cloud_folder_id": False,
            "sync_client_id": False,
        }
        binary_content = client.download_file_o(drive_id=self.onedrive_key, drive_item=cloud_key)
        result.update({"raw": binary_content})
        return result
