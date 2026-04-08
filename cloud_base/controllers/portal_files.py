# -*- coding: utf-8 -*-

import base64
from collections import OrderedDict

from odoo import _, fields, http, SUPERUSER_ID
from odoo.addons.portal.controllers.portal import get_records_pager, CustomerPortal, pager as portal_pager
from odoo.http import request
from odoo.tools import consteq
from odoo.tools.safe_eval import safe_eval


class CustomerPortal(CustomerPortal):
    """
    Overwritting the controller to show shared pages
    """
    def _prepare_home_portal_values(self, counters):
        """
        Overwrite to understand wheter the portal entry should be shown

        Methods:
         * _return_partner_share_domain
        """
        values = super(CustomerPortal, self)._prepare_home_portal_values(counters)
        if "shares_count" in counters and request.env.user.has_group("cloud_base.group_cloud_base_share"):
            shares_count = request.env["clouds.share"].search_count(self._return_partner_share_domain())
            if shares_count:
                values.update({"shares_count": shares_count or False})
        return values

    def _check_settings_and_token(self, shareint, sharetoken=None):
        """
        The method to check whether share is permitted for the current user

        Args:
         * shareint - int
         * sharetoken - str

        Methods:
         * _check_active

        Returns:
         * clouds.share object under sudo
        """
        share_id = False
        if request.env.user.has_group("cloud_base.group_cloud_base_share"):
            if sharetoken:
                if shareint is not None:
                    share_id = request.env["clouds.share"].sudo().with_user(SUPERUSER_ID).browse(shareint)
                else:
                    share_id = request.env["clouds.share"].sudo().with_user(SUPERUSER_ID).search([
                        ("access_token", "=", sharetoken)
                    ], limit=1)
                if not share_id or not share_id.exists() or not share_id.allow_by_token \
                        or not consteq(share_id.access_token, sharetoken) or not share_id._check_active():
                    share_id = False
            else:
                share_id = request.env["clouds.share"].browse(shareint)
                if not share_id or not share_id.exists() or not share_id._check_active():
                    # done before superuser to simulate check user rights in _check_active
                    share_id = False
                else:
                    share_id = share_id.sudo().with_user(SUPERUSER_ID)
        return share_id

    def _return_partner_share_domain(self):
        """
        The method to prepare the domain for the current user partner vaults

        Returns:
         * list (RPR)
        """
        partner_id = request.env.user.partner_id.id
        com_partner_id = request.env.user.partner_id.commercial_partner_id.id
        return [
            ("active", "=", True),
            "|", ("active_till", "=", False), ("active_till", ">", fields.Datetime.now()),
            "|", ("partner_ids", "in", partner_id), ("partner_ids", "=", com_partner_id)
        ]

    def _return_search_in_share(self, search_in, search):
        """
        Returns:
         * list - domain to search
        """
        search_domain = []
        if search_in in ("name"):
            search_domain = [("name", "ilike", search)]
        elif search_in in ("folder_id"):
            search_domain = [("clouds_folder_id.name", "ilike", search)]
        elif search_in in ("cloud_tag_ids"):
            search_domain = [("cloud_tag_ids.name", "ilike", search)]
        return search_domain

    def _return_searchbar_sortings_share(self, values):
        """
        Returns:
         * dict
            ** search_by_sortings - {}
            ** searchbar_inputs - {}

        Extra info:
         * for databases exist prior to search_name_key, sorting might work incorrect. It is needed to update
           either name or pubslihed name to trigger inverse
        """
        website_id = request.website
        searchbar_sortings = {
            "name": {"label": _("Name"), "order": "name asc, id desc"},
            "folder_id": {"label": _("Folder"), "order": "clouds_folder_id desc, id desc"},
        }
        searchbar_inputs = {
            "name": {"input": "name", "label": _("Name")},
            "folder_id": {"input": "folder_id", "label": _("Search by folder")},
            "cloud_tag_ids": {"input": "cloud_tag_ids", "label": _("Search by tags")},
        }
        return {
            "searchbar_sortings": searchbar_sortings,
            "searchbar_inputs": searchbar_inputs,
        }

    def _prepare_share_helper(self, share_id, page=1, folders=None, tags=None, sortby=None, search=None,
        search_in="content", domain=[], url="/clouds/share", **kw):
        """
        The helper method to get attachments
        """
        values = {}
        domain += [("id", "in", share_id.shared_attachment_ids.ids)]
        attachment_object = request.env["ir.attachment"].sudo()
        if not sortby:
            sortby = "name"
        searches_res = self._return_searchbar_sortings_share(values)
        searchbar_sortings = searches_res.get("searchbar_sortings")
        searchbar_inputs = searches_res.get("searchbar_inputs")
        if not searchbar_sortings.get(sortby):
            sortby = "name"
        sort_order = searchbar_sortings[sortby]["order"]
        if search and search_in:
            search_domain = self._return_search_in_share(search_in, search)
            domain += search_domain
        attachments_count_count = attachment_object.search_count(domain)
        items_num = self._items_per_page
        pager = portal_pager(
            url=url,
            url_args={"sortby": sortby, "search": search, "search_in": search_in, "folders": folders, "tags": tags},
            total=attachments_count_count,
            page=page,
            step=items_num,
        )
        attachment_ids = attachment_object.search(domain, order=sort_order, limit=items_num, offset=pager["offset"])
        values.update({
            "full_domain": domain,
            "attachment_ids": attachment_ids,
            "pager": pager,
            "searchbar_sortings": searchbar_sortings,
            "searchbar_inputs": searchbar_inputs,
            "search_in": search_in,
            "sortby": sortby,
        })
        if search:
            values.update({"done_search": search})
        return values

    def _prepare_shares_helper(self, page=1, search=None, domain=[], url="/clouds/shares", **kw):
        """
        The helper method for locations list

        Returns:
         * dict
        """
        values = {}
        share_object = request.env["clouds.share"]
        if search:
            domain.append(("name", "ilike", search))
        items_num = self._items_per_page
        pager = portal_pager(
            url=url,
            url_args={"search": search},
            total=share_object.search_count(domain),
            page=page,
            step=items_num,
        )
        share_ids = share_object.search(domain, limit=items_num, offset=pager["offset"])
        values.update({
            "share_ids": share_ids,
            "pager": pager,
            "searchbar_inputs": {"name": {"input": "name", "label": _("Name")}},
            "search_in": "name",
        })
        return values

    def _prepare_vals_share(self, share_id, sharetoken=None, page=1, folders=None, tags=None, sortby=None, search=None,
        search_in="name", **kw):
        """
        The method to prepare values for attachments
        """
        domain = []
        show_folders, show_tags = share_id.show_folders, share_id.show_tags
        user_tags = request.env.user.has_group("cloud_base.group_cloud_base_tags")
        url="/clouds/share/{}{}".format(share_id.id, sharetoken and "/token/{}".format(sharetoken) or "")
        if folders and show_folders:
            folders_lsit = folders.split(",")
            folder_int_list = [int(item) for item in folders_lsit]
            domain += [("clouds_folder_id", "in", folder_int_list)]
        if tags and user_tags and show_tags:
            tags_list = tags.split(",")
            tags_int_list = [int(item) for item in tags_list]
            tags_number = len(tags_int_list) - 1
            itera = 0
            while itera != tags_number:
                domain += ["|"]
                itera += 1
            for tag_u in tags_int_list:
                domain += [("cloud_tag_ids", "=", tag_u)]
        values = self._prepare_share_helper(
            share_id, page=page, folders=folders, tags=tags, sortby=sortby, search=search, search_in=search_in,
            domain=domain, url=url, **kw
        )
        selected_folder, selected_folder_name = 0, ""
        if share_id.allow_uploading:
            selected_folder = show_folders and kw.get("selected_folder") or share_id.uploading_folder_id.id
            if selected_folder:
                selected_folder_name = request.env["clouds.folder"].sudo().browse(int(selected_folder)).name
        values.update({
            "page_name": _("Share"),
            "default_url": "/clouds/share",
            "share_id": share_id,
            "folders": folders,
            "tags": tags,
            "show_folders": show_folders,
            "show_tags": show_tags and user_tags,
            "allow_slideshow": share_id.allow_slideshow,
            "selected_folder": selected_folder,
            "selected_folder_name": selected_folder_name,
            "allow_adding_folders": share_id.show_folders and share_id.allow_adding_folders or False,
        })
        request.session["all_attachments"] = values.get("attachment_ids").ids[:100]
        return values

    def _prepare_vals_shares(self, page=1, search=None, **kw):
        """
        The method to prepare values for locations list

        Returns:
         * dict
        """
        domain = self._return_partner_share_domain()
        url="/clouds/shares"
        values = self._prepare_shares_helper(page=page, search=search, domain=domain, url=url, **kw)
        values.update({"page_name": _("My Shares"), "default_url": "/clouds/shares"})
        request.session["all_shares"] = values.get("share_ids").ids[:100]
        return values

    @http.route(["/clouds/shares/", "/clouds/shares/page/<int:page>"], type="http", auth="user", website=True,
        sitemap=False)
    def cloud_base_shares(self, page=1, search=None, search_in="name", **kw):
        """
        The route to open the portal shares
        """
        if not request.env.user.has_group("cloud_base.group_cloud_base_share"):
            return request.render("http_routing.404")
        values = self._prepare_vals_shares(page=page, search=search, **kw)
        res = request.render("cloud_base.shares_list", values)
        return res

    @http.route([
        "/clouds/share/<int:shareint>",
        "/clouds/share/<int:shareint>/page/<int:page>",
        "/clouds/share/<int:shareint>/token/<sharetoken>",
        "/clouds/share/<int:shareint>/token/<sharetoken>/page/<int:page>",
        "/clouds/share/token/<sharetoken>",
    ], type="http", auth="public", website=True, sitemap=False)
    def cloud_base_share(self, shareint=None, sharetoken=None, page=1, folders=None, tags=None, sortby=None,
        search=None, search_in="name", **kw):
        """
        The route to open the portal share

        Methods:
         * _check_settings_and_token
         * _prepare_vals_share
        """
        share_id = self._check_settings_and_token(shareint, sharetoken)
        if not share_id:
            return request.render("http_routing.404")
        values = self._prepare_vals_share(
            share_id, sharetoken, page=page, folders=folders, tags=tags, sortby=sortby, search=search,
            search_in=search_in, **kw
        )
        values.update({"sharetoken": sharetoken})
        res = request.render("cloud_base.cloud_shares", values)
        return res

    @http.route([
        "/clouds/share/upload/<int:shareint>",
        "/clouds/share/upload/<int:shareint>/<string:res_model>/<int:res_id>",
        "/clouds/share/upload/<int:shareint>/token/<sharetoken>",
        "/clouds/share/upload/<int:shareint>/<string:res_model>/<int:res_id>/token/<sharetoken>"
    ], type="http", auth="public", website=True, sitemap=False)
    def share_download_file_manager(self, shareint, sharetoken=None, res_model=None, res_id=None, **kwargs):
        """
        The method to prepare all share attachments for downloading

        Methods:
         * _check_settings_and_token
         * _download_as_archive of ir.attachment
         * _download_as_attachment of ir.attachment
        """
        share_id = self._check_settings_and_token(shareint, sharetoken)
        if not share_id:
            return request.render("http_routing.404")
        if res_model and res_id:
            # a particular attachment/folder/tag is donwloaded
            if res_model == "ir.attachment":
                return request.env["ir.attachment"].sudo().browse(res_id)._download_as_attachment()
            elif res_model == "clouds.folder":
                folder_name = request.env["clouds.folder"].sudo().browse(res_id).name
                attachment_ids = request.env["ir.attachment"].sudo().search([
                    ("clouds_folder_id", "=", res_id), ("id", "in", share_id.shared_attachment_ids.ids)
                ])
                content, headers = attachment_ids._download_as_archive(folder_name)
                return request.make_response(content, headers)
            elif res_model == "clouds.tag":
                tag_name = request.env["clouds.tag"].sudo().browse(res_id).name
                attachment_ids = request.env["ir.attachment"].sudo().search([
                    ("cloud_tag_ids", "=", res_id), ("id", "in", share_id.shared_attachment_ids.ids)
                ])
                content, headers = attachment_ids._download_as_archive(tag_name)
                return request.make_response(content, headers)
        else:
            # whe whole share is downloaded
            content, headers = share_id.shared_attachment_ids._download_as_archive(share_id.name)
            return request.make_response(content, headers)
        return request.render("http_routing.404")

    @http.route([
        "/clouds/share/create/<int:shareint>/<string:res_model>",
        "/clouds/share/create/<int:shareint>/<string:res_model>/token/<sharetoken>"
    ], type="json", auth="public", website=True, sitemap=False)
    def share_create_node(self, shareint, sharetoken=None, res_model=None, **kwargs):
        """
        The method to prepare all share attachments for downloading

        Methods:
         * _check_settings_and_token
        """
        share_id = self._check_settings_and_token(shareint, sharetoken)
        if not share_id:
            return False
        if (res_model == "clouds.folder" and (not share_id.allow_adding_folders or not share_id.show_folders)) \
                or (res_model == "clouds.tag" and (not share_id.allow_adding_tags or not share_id.show_tags)):
            return False
        if res_model:
            if res_model == "clouds.folder":
                node_id = request.env["clouds.folder"].sudo().action_create_node(kwargs.get("data"))
                share_id.write({"folder_ids": [(4, node_id.get("id"))]})
                return node_id.get("id")
            else:
                node_id = request.env["clouds.tag"].sudo().action_create_node("clouds.tag", kwargs.get("data"))
                share_id.write({"tag_ids": [(4, node_id.get("id"))]})
                return node_id
            return True
        return False

    @http.route(["/clouds/share/add/<int:shareint>", "/clouds/share/add/<int:shareint>/token/<sharetoken>"],
        type="http", auth="public", methods=["POST"], csrf=False, website=True, sitemap=False)
    def share_upload_file_manager(self, shareint, sharetoken=None, **kwargs):
        """
        The method to add attachments to the share selected folder

        Methods:
         * _check_settings_and_token
        """
        share_id = self._check_settings_and_token(shareint, sharetoken)
        folder_id = kwargs.get("selected_folder")
        redirectn = not kwargs.get("noredirect")
        if not share_id or not share_id.allow_uploading or not folder_id or folder_id == "0":
            return redirectn and request.render("http_routing.404") or ""
        folder_id = int(folder_id)
        attachment_vals = []
        files = request.httprequest.files.getlist("ufile")
        for file in files:
            filename = file.filename
            if request.httprequest.user_agent.browser == "safari":
                filename = unicodedata.normalize("NFD", file.filename)
            attachment_vals.append({
                "name": filename,
                "clouds_folder_id": folder_id,
                "datas": base64.encodebytes(file.read()),
                "type": "binary",
                "mimetype": file.content_type,
                "share_ids": [(6, 0, share_id.ids)],
            })
        if attachment_vals:
            request.env["ir.attachment"].sudo().create(attachment_vals)
        subquery = "?folders={}&selected_folder={}".format(folder_id, folder_id)
        redirection = "/clouds/share/{}{}".format(shareint, subquery)
        if sharetoken is not None:
            redirection = "/clouds/share/{}/token/{}{}".format(shareint, sharetoken, subquery)
        return redirectn and request.redirect(redirection) or ""

    @http.route([
        "/clouds/share/slideshow/<int:shareint>",
        "/clouds/share/slideshow/<int:shareint>/token/<sharetoken>"
    ], type="json", auth="public", website=True, sitemap=False)
    def share_donwnload_attachments(self, shareint, sharetoken=None, attachments_domain="[]", **kwargs):
        """
        The method to prepare all share attachments for downloading

        Methods:
         * _check_settings_and_token
         * action_get_images of ir.attachment
        """
        share_id = self._check_settings_and_token(shareint, sharetoken)
        if not share_id:
            return False
        core_url =  "/clouds/share/upload/{}/ir.attachment/".format(shareint) + "{}"
        if sharetoken:
            core_url += "/token/" + sharetoken
        attachments = request.env["ir.attachment"].sudo().search(safe_eval(attachments_domain))
        images = attachments.action_get_images(core_url)
        return images

    @http.route([
        "/clouds/share/get_nodes/<int:shareint>/<string:res_model>",
        "/clouds/share/get_nodes/<int:shareint>/<string:res_model>/token/<sharetoken>",
    ], type="json", auth="public", website=True, sitemap=False)
    def cloud_base_get_nodes(self, shareint, sharetoken=None, res_model=None):
        """
        The route to prepare jstree navigation

        Methods:
         * _check_settings_and_token
         * _prepare_vals_share
        """
        nodes_list = []
        share_id = self._check_settings_and_token(shareint, sharetoken)
        if share_id:
            if res_model == "clouds.folder":
                if share_id.show_folders:
                    folder_ids = share_id.action_get_share_folders() \
                        | share_id.shared_attachment_ids.mapped("clouds_folder_id")
                    nodes_list = folder_ids._return_nodes_with_restriction()
            elif res_model == "clouds.tag":
                if share_id.show_tags:
                    tag_ids = share_id.action_get_share_tags() | share_id.shared_attachment_ids.mapped("cloud_tag_ids")
                    nodes_list = tag_ids._return_nodes_with_restriction()
        return nodes_list

    @http.route([
        "/clouds/share/get_setting/<int:shareint>/<string:res_model>",
        "/clouds/share/get_setting/<int:shareint>/<string:res_model>/token/<sharetoken>",
    ], type="json", auth="public", website=True, sitemap=False)
    def cloud_base_get_settings(self, shareint, sharetoken=None, res_model=None):
        """
        The route to prepare jstree navigation

        Methods:
         * _check_settings_and_token
         * _prepare_vals_share

        Returns:
         * dict
        """
        allow_create, allow_search = False, False
        share_id = self._check_settings_and_token(shareint, sharetoken)
        if share_id:
            if res_model == "clouds.folder":
                if  share_id.show_folders:
                    allow_create = share_id.allow_adding_folders
                    allow_search = share_id.allow_folders_search
            elif res_model == "clouds.tag":
                if  share_id.show_tags:
                    allow_create = share_id.allow_adding_tags
                    allow_search = share_id.allow_tags_search
        return {
            "allow_create": allow_create,
            "allow_search": allow_search,
        }
