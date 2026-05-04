# -*- coding: utf-8 -*-

import logging
import requests

_logger = logging.getLogger(__name__)

try:
    from microsoftgraph.client import Client
    from microsoftgraph.decorators import token_required
    from microsoftgraph import exceptions
except ImportError as e:
    _logger.error(e)
    OnedriveApiClient = object


class OnedriveApiClient(Client):
    """
    Rw-write to introduce own API methods
    """
    BASEONEDRIVEURL = "https://graph.microsoft.com/v1.0"

    def __init__(self, client_id, client_secret, api_version="v1.0", account_type="common", requests_hooks=None,
                 cloud_client=False):
        """
        Re-write to link clouds.client
        """
        super(OnedriveApiClient, self).__init__(
            client_id=client_id, client_secret=client_secret, api_version=api_version, account_type=account_type,
            requests_hooks=requests_hooks
        )
        self.clouds_client = cloud_client
        self._client = self

    def _get(self, url, **kwargs):
        return self._request("GET", url, **kwargs)

    def _put_not_json(self, url, no_token=False, **kwargs):
        """
        The method to request put command to Microsoft Graph API
        """
        return self._request_not_json("PUT", url, no_token=no_token, **kwargs)

    def _request_not_json(self, method, url, headers=None, content_type="multipart/form-data", no_token=False,
                          **kwargs):
        """
        The method to request not in "application/json" format (Microsoft graph library doesn"t support others)
        """
        _headers = {"Accept": "application/json", "Content-Type": content_type}
        if not no_token:
            # Sometimes, e.g. in case of multi upload sessions put, we should not pass token (it might lead to 401)
            _headers.update({"Authorization": "Bearer " + self.token["access_token"],})
        if headers:
            _headers.update(headers)
        return self._parse(requests.request(method, url, headers=_headers, **kwargs))

    def _get_content(self, url, **kwargs):
        """
        Re-write to parse "content" of files
        """
        return self._request_content("GET", url, **kwargs)

    def _request_content(self, method, url, headers=None, **kwargs):
        """
        Re-write to parse "content" of files
        """
        _headers = {"Accept": "application/json", "Authorization": "Bearer " + self.token["access_token"]}
        if headers:
            _headers.update(headers)
        if "files" not in kwargs:
            # If you use the "files" keyword, the library will set the Content-Type to multipart/form-data
            # and will generate a boundary.
            _headers["Content-Type"] = "application/json"
        return self._parse_content(requests.request(method, url, headers=_headers, **kwargs))

    def _parse_content(self, response, **kwargs):
        """
        Re-write to parse "content" of files
        """
        self._parse(response=response) # to process errors
        try:
            res = response.content
        except:
            res = response.text
        return res

    @token_required
    def sharepoint_site_o(self, path, params=None):
        """
        Method to return sharepoint site

        Args:
         * path in a specified format. e.g. odootools.sharepoint.com:/sites/odootoolstest (without https:!)
           or just "root"

        Returns:
         * dict
        """
        url = "{}/sites/{}".format(self.BASEONEDRIVEURL, path)
        res = self._get(url, params=params)
        return res

    @token_required
    def drives_list_o(self, site_id, params=None):
        """
        The method to return all drives (document libraries) of sharepoint site

        Methods:
         * site_id - id of Sharepoint site

        Returns:
         * dict. Dict["value"] contains list of drives with ID
        """
        url = "{}/sites/{}/drives".format(self.BASEONEDRIVEURL, site_id)
        res = self._get(url, params=params)
        return res

    @token_required
    def personal_drive_o(self, params=None):
        """
        The method to return drive of personal / business account
        """
        url = "{}/me/drive".format(self.BASEONEDRIVEURL)
        res = self._get(url, params=params)
        return res

    @token_required
    def children_items_o(self, drive_id, drive_item_id, params=None):
        """
        The method to return children items of this drive
        API returns max 200 items + url for the next request. Thus, we should be in while loop

        Args:
         * drive_id - id of Drive
         * drive_item_id - id of DriveItem

        Returns:
         * list of dicts
        """
        url = "{}/drives/{}/items/{}/children?$top=100".format(self.BASEONEDRIVEURL, drive_id, drive_item_id)
        res = []
        while url:
          respo = self._get(url, params=params)
          res += respo.get("value")
          url = respo.get("@odata.nextLink") or False
        return res

    @token_required
    def get_drive_item_o(self, drive_id, drive_item_id, params=None):
        """
        The method to get OneDrive item by id

        Args:
         * drive_id - id of Drive
         * drive_item_id - id of DriveItem

        Returns:
         * dict
        """
        url = "{}/drives/{}/items/{}".format(self.BASEONEDRIVEURL, drive_id, drive_item_id)
        res = self._get(url, params=params)
        return res

    @token_required
    def create_folder_o(self, drive_id, folder_name, parent="root", params=None):
        """
        The method to create a new folder in Onedrive

        Args:
         * drive_id - Drive object id
         * folder_name - char - new folder name
         * parent - DriveItem object id or string - parent folder. If string, it should be always "root"
        """
        data = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }
        url = "{}/drives/{}/items/{}/children".format(self.BASEONEDRIVEURL, drive_id, parent)
        res = self._post(url, json=data, params=params)
        return res

    @token_required
    def move_or_update_item_o(self, drive_id, drive_item_id, new_parent=False, new_name=False, params=None):
        """
        The method to move a folder/file to a new parent (if parent is defined) or update a name (if new_name
        is defined)

        Args:
         * drive_id - Drive object id
         * drive_item_id - Drive item id
         * new_parent - DriveItem object id or string - new parent folder
         * new_name - char - new DriveItem name
        """
        data = {}
        if new_name:
            data.update({"name": new_name})
        if new_parent:
            data.update({
                "parentReference": {"id": new_parent},
            })
        res = False
        if data:
            url = "{}/drives/{}/items/{}".format(self.BASEONEDRIVEURL, drive_id, drive_item_id)
            res = self._patch(url, json=data, params=params)
        else:
            self.clouds_client._cloud_log(False, "No parent id and no new name were defined")
        return res

    @token_required
    def upload_file_o(self, drive_id, folder_name, file_name, content, mimetype, params=None):
        """
        The method to upload a new file (<4mb).

        Args:
         * drive_id - Drive object id
         * folder_name - DriveItem object - parent folder
         * file_name - the name of uploaded file
         * content - binary
         * mimetype - request content type, e.g. image/jpg

        Extra info:
         *  This method doesn't support duplicated names check, USE upload_large_file_o
        """
        url = "{}/drives/{}/items/{}:/{}:/content".format(self.BASEONEDRIVEURL, drive_id, folder_name, file_name)
        res = self._put_not_json(url=url, content_type=mimetype, data=content, params=params)
        return res

    @token_required
    def upload_large_file_o(self, drive_id, folder_name, file_name, path, file_size, params=None):
        """
        The method to upload a new file (>= 4mb)

        Args:
         * drive_id - Drive object id
         * folder_name - DriveItem object - parent folder
         * file_name - the name of uploaded file
         * content - binary
         * file_size - integer

        Methods:
         * generate_upload_session_o
        """
        chunk_size = 8 * 1024 * 1024 # 8Mb chunks
        with open(path, "rb") as f:
            upload_session = self.generate_upload_session_o(
                drive_id=drive_id, folder_name=folder_name, file_name=file_name, params=params
            ).get("uploadUrl")
            uploaded_bytes = 0
            while uploaded_bytes < file_size:
                chunk = f.read(chunk_size)
                chunk_length = len(chunk)
                end_byte = uploaded_bytes + chunk_length - 1
                headers = {
                    "Content-Length": str(chunk_length),
                    "Content-Range": f"bytes {uploaded_bytes}-{end_byte}/{file_size}"
                }
                upload_file = self._put_not_json(
                    url=upload_session, content_type="application/json", headers=headers, no_token=True, params=params,
                    data=chunk,
                )
                if upload_file.get("error"):
                    self._delete(upload_session)
                    self.clouds_client._cloud_log(False, "The file was not uploaded. Error: {}".format(upload_file))
                    res = False
                    break
                else:
                    res = upload_file
                    uploaded_bytes += chunk_length
        return res

    @token_required
    def generate_upload_session_o(self, drive_id, folder_name, file_name, params=None):
        """
        The method to prepare an Upload session for a large file

        Args:
         * drive_id - Drive object id
         * folder_name - DriveItem object - parent folder
        """
        data = {"item": {"@microsoft.graph.conflictBehavior": "rename"}}
        url = "{}/drives/{}/items/{}:/{}:/createUploadSession".format(
            self.BASEONEDRIVEURL, drive_id, folder_name, file_name,
        )
        res = self._post(url, json=data, params=params)
        return res

    @token_required
    def download_file_o(self, drive_id, drive_item, params=None):
        """
        The method to download a file from Onedrive

        Args:
         * drive_id - id of Drive
         * drive_item - id of DriveItem

        Returns:
         * dict
        """
        url = "{}/drives/{}/items/{}/content".format(self.BASEONEDRIVEURL, drive_id, drive_item)
        res = self._get_content(url=url)
        return res

    @token_required
    def delete_file_o(self, drive_id, drive_item_id, params=None):
        """
        The method to delet item.

        Args:
         * drive_id - Drive object id
         * drive_item_id - DriveItem to delete
        """
        url = "{}/drives/{}/items/{}".format(self.BASEONEDRIVEURL, drive_id, drive_item_id)
        res = self._delete(url, params=params)
        return res

    def _parse(self, response):
        """
        Fully re-write since there is a critical error in response.headers["Content-Type"], which is not always present
        """
        status_code = response.status_code
        if status_code in [204, 404]:
            raise exceptions.NotFound("Item was not found")
        if response.headers.get("Content-Type") and "application/json" in response.headers["Content-Type"]:
            r = response.json()
        else:
            r = response.content

        if status_code in (200, 201, 202):
            return r
        elif status_code == 400:
            raise exceptions.BadRequest(r)
        elif status_code == 401:
            raise exceptions.Unauthorized(r)
        elif status_code == 403:
            raise exceptions.Forbidden(r)
        elif status_code == 405:
            raise exceptions.MethodNotAllowed(r)
        elif status_code == 406:
            raise exceptions.NotAcceptable(r)
        elif status_code == 409:
            raise exceptions.Conflict(r)
        elif status_code == 410:
            raise exceptions.Gone(r)
        elif status_code == 411:
            raise exceptions.LengthRequired(r)
        elif status_code == 412:
            raise exceptions.PreconditionFailed(r)
        elif status_code == 413:
            raise exceptions.RequestEntityTooLarge(r)
        elif status_code == 415:
            raise exceptions.UnsupportedMediaType(r)
        elif status_code == 416:
            raise exceptions.RequestedRangeNotSatisfiable(r)
        elif status_code == 422:
            raise exceptions.UnprocessableEntity(r)
        elif status_code == 429:
            raise exceptions.TooManyRequests(r)
        elif status_code == 500:
            raise exceptions.InternalServerError(r)
        elif status_code == 501:
            raise exceptions.NotImplemented(r)
        elif status_code == 503:
            raise exceptions.ServiceUnavailable(r)
        elif status_code == 504:
            raise exceptions.GatewayTimeout(r)
        elif status_code == 507:
            raise exceptions.InsufficientStorage(r)
        elif status_code == 509:
            raise exceptions.BandwidthLimitExceeded(r)
        else:
            if r.get("error") and r.get("error").get("innerError") \
                    and r.get("error").get("innerError").get("code") == "lockMismatch":
                # File is currently locked due to being open in the web browser
                # while attempting to reupload a new version to the drive.
                # Thus temporarily unavailable.
                raise exceptions.ServiceUnavailable(r)
            raise exceptions.UnknownError(r)
