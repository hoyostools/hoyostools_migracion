# -*- coding: utf-8 -*-

import json
from sortedcontainers import SortedList

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class clouds_tree_mixin(models.AbstractModel):
    """
    This is the Abstract Model to introduce jstree methods
    Primarily used to distinct real folder methods and jstree ones
    """
    _name = "clouds.tree.mixin"
    _description = "Cloud Mixin"

    @api.constrains("parent_id")
    def _check_node_recursion(self):
        """
        Constraint for recursion
        """
        if not self._context.get("prepare_queue_context") and not self._check_recursion():
            raise ValidationError(_("Recursions are not allowed!"))
        return True

    sequence = fields.Integer(string="Sequence", default=0)
    active = fields.Boolean(string="Active", default=True, index=True)
    description = fields.Text(string="Notes", translate=True)

    @api.model
    def action_return_mass_actions(self):
        """
        The method to return available mass actions in js format

        Returns:
         * list of dict
           ** id
           ** name
        """
        result = []
        self = self.sudo()
        Config = self.env["ir.config_parameter"].sudo()
        mass_actions_list = safe_eval(Config.get_param("cloud_base.ir_actions_server_ids", "[]"))
        mass_action_ids = self.env["ir.actions.server"].search([("id", "in", mass_actions_list)])
        for mass_action in mass_action_ids:
            if not mass_action.groups_id or (self.env.user.groups_id & mass_action.groups_id):
                result.append({"id": mass_action.id, "name": mass_action.name})
        return result

    @api.model
    def action_proceed_mass_action(self, att_list, action_id):
        """
        The method to trigger mass action for selected passwords

        Args:
         * att_list - list of ints (selected attachments IDs)
         * action_id - int - ir.actions.server id

        Methods:
         * run() of ir.actions.server

        Returns:
         * dict: either action dict, or special view dict, or empty dict if no result
           The special case is for the deletion where we pass the only key delete True, since we should force
           full reselection (attachments are not deleted but they are marked for deletion)

        Extra info:
         * we use api@model with search to make sure each record exists (e.g. deleted in meanwhile)
        """
        attachment_ids = self.env["ir.attachment"].with_context(active_test=False).search([("id", "in", att_list)])
        result = {}
        if attachment_ids:
            action_server_id = self.env["ir.actions.server"].browse(action_id)
            if action_server_id.exists():
                action_context = {
                    "active_id": attachment_ids[0].id,
                    "active_ids": attachment_ids.ids,
                    "active_model": "ir.attachment",
                    "record": attachment_ids[0],
                    "records": attachment_ids,
                }
                result = action_server_id.with_context(action_context).run()
                if self.sudo().env.ref("cloud_base.ir_attachment_mass_delete") == action_server_id:
                    result = {"delete": True}
                elif result and result.get("type"):
                    local_context = {}
                    if result.get("context"):
                        local_context = result.get("context")
                        if not isinstance(local_context, dict):
                            local_context = json.loads(result.get("context"))
                    local_context.update({"default_attachment_ids": [(6, 0, attachment_ids.ids)]})
                    result["context"] = local_context
        return result or {}

    @api.model
    def action_get_hierarchy(self, key, res_model=False, res_id=False):
        """
        The method to get hirarchy of KPI targets

        Args:
         * key - string - the reference

        Methods:
         * action_return_nodes of kpi.category
         * action_js_find_folders_by_res_params

        Returns:
         * list of dicts
        """
        result = []
        if key == "folders":
            if res_model and res_id:
                result = self.env["clouds.folder"].action_js_find_folders_by_res_params(res_model, res_id)
            else:
                result = self.env["clouds.folder"].action_return_nodes()
        return result

    @api.model
    def action_return_nodes(self):
        """
        The method to recursively preare hirarchy of directories (for JS minaly)

        Methods:
         * _return_nodes_recursive

        Returns:
         * list of folders dict with keys:
           ** id
           ** text - folder_name
           ** icon
           ** children - array with the same keys

        Extra info:
         * we should not move by folders without parent, but should move by a parent without AVAILABLE for this user
           parent. So, to show "Tasks", if "Projects" are not available.
           That's why we have to run the method under sudo and then clear items
         * SortedList is critical for performance on large numbers (e.g. 100k items) for checking "id in list"
        """
        res = []
        all_nodes = self.search([])
        if all_nodes:
            nodes = all_nodes.filtered(lambda fol: not fol.parent_id or fol.parent_id not in all_nodes)
            all_ids = SortedList(all_nodes.ids)
            edit_ids = SortedList(self.with_context(write_mode=True).search([]).ids)
            for node in nodes:
                res += node._return_nodes_recursive(all_ids, edit_ids)
        return res

    @api.model
    def action_js_find_folders_by_res_params(self, res_model, res_id):
        """
        The method to search for ab object folder

        Args:
         * res_model - char - name of checked folder
         * res_id - int

        Methods:
         * _return_nodes_recursive

        Returns:
         * list of dicts (actually this list would always have a single element or no element):
           see _return_nodes_recursive

        Extra info:
         * if folder_id exists, but it is not available for this user, we do not try to show available children
           as it is done in the full jstree. The reason is that if object own folder is not available, no sense
           to show attachment box at all
        """
        folder_id = self.search([("res_model", "=", res_model), ("res_id", "=", res_id)], limit=1)
        res = False
        if folder_id:
            all_ids = SortedList(self.search([("id", "child_of", folder_id.id)]).ids)
            edit_ids = SortedList(self.with_context(write_mode=True).search([("id", "child_of", folder_id.id)]).ids)
            res = folder_id._return_nodes_recursive(all_ids, edit_ids)[0]
        return res and [res] or []

    @api.model
    def action_create_node(self, data):
        """
        The method to update node name

        Methods:
         * _order_node_after_dnd
         * action_js_format_folder_for_js_tree

        Returns:
         * dict of keys for js tree (except "children") or False if error (mainly access rights warning)
        """
        name = data.get("text")
        parent_id = data.get("parent")
        if parent_id == "#":
            parent_id = False
        else:
            parent_id = int(parent_id)
        new_node_vals = {"name": name, "parent_id": parent_id}
        new_node = self.create([new_node_vals])
        new_node.with_context(ir_attachment_security=True)._order_node_after_dnd(parent_id=parent_id, position=False)
        return new_node.action_js_format_folder_for_js_tree()

    def action_update_node(self, data, position):
        """
        The method to update node name

        Args:
         * data - dict of node params
         * position - false (in case it is rename) or int (in case it is move)

        Methods:
         * _order_node_after_dnd

        Returns:
         * dict of keys for js tree (except "children") or False if error (mainly access rights warning)

        Extra info:
         * Expected singleton
        """
        new_name = data.get("text")
        new_parent_id = data.get("parent")
        new_parent_id = new_parent_id != "#" and int(new_parent_id) or False
        if self.name != new_name:
            self.name = new_name
        if self.parent_id.id != new_parent_id:
            self.parent_id = new_parent_id
        if position is not False:
            self._order_node_after_dnd(parent_id=new_parent_id, position=position)
        return self.action_js_format_folder_for_js_tree()

    def action_delete_node(self):
        """
        The method to deactivate a node
        It triggers recursive deactivation of children

        Returns:
         * int - id of udpated record

        Extra info:
         * Expected singleton
        """
        self.active = False
        return True

    def action_js_format_folder_for_js_tree(self, all_nodes=None, edit_nodes=None):
        """
        The method to prepare dict for node

        Args:
         * all_nodes - list of ids of clouds.folder which are available for the current user
         * edit_nodes - list of ids of clouds.folder which are available for the current user for update

        Returns:
        * dict
         ** text - char
         ** id - int
         ** icon - char
         ** data - dict:
           *** url - char
           *** rule_related - boolean (whether created by auto rule)
           *** res_model - char
           *** res_id - char
           *** edit_rights - right to change folder

        Extra info:
         * edit_right relies upon edit_nodes, since if a user initially doesn't have edit rights, this user
           will not be able to update a node and get here. In critical case, check would be done on Python level
         * Expected singleton
        """
        result = False
        cur_id = self.id
        if all_nodes is None or cur_id in all_nodes:
            custom_data = {
                "url": self.url,
                "rule_related": self.rule_id and True or False,
                "res_model": self.res_model,
                "res_id": self.res_id,
                "edit_right": (edit_nodes is None or cur_id in edit_nodes) and True or False,
            }
            result = {"text": self.name, "id": cur_id, "icon": self.icon_class, "data": custom_data}
        return result

    def action_js_format_folder_for_js_tree_web(self, all_nodes=None):
        """
        The method to prepare dict for node

        Args:
         * all_nodes - list of ids of clouds.folder which are available for the current user
         * edit_nodes - list of ids of clouds.folder which are available for the current user for update

        Returns:
        * dict
         ** text - char
         ** id - int
         ** icon - char
         ** data - dict:
           *** url - char
           *** rule_related - boolean (whether created by auto rule)
           *** res_model - char
           *** res_id - char
           *** edit_rights - right to change folder

        Extra info:
         * edit_right relies upon edit_nodes, since if a user initially doesn't have edit rights, this user
           will not be able to update a node and get here. In critical case, check would be done on Python level
         * Expected singleton
        """
        result = False
        cur_id = self.id
        if all_nodes is None or cur_id in all_nodes:
            result = {"text": self.name, "id": cur_id}
        return result

    def _return_nodes_recursive(self, all_nodes=[], edit_nodes=[]):
        """
        The method to go by all nodes recursively to prepare their list in js_tree format

        Methods:
         * action_js_format_folder_for_js_tree

        Args:
         * all_nodes - SortedList of ids of clouds.folder which are available for the current user
         * edit_nodes - - SortedList of ids of clouds.folder which are available for the current user for update
           Used to avoid checking rights for each node

        Returns:
         * list of dicts (see action_js_format_folder_for_js_tree)

        Extra info:
         * we are under sudo to make sure all children are returned, but we show only those to which the current
           user has an access
         * Expected singleton
        """
        self = self.sudo()
        res = self.action_js_format_folder_for_js_tree(all_nodes, edit_nodes) or {}
        child_res = []
        for child in self.child_ids:
            child_values = child._return_nodes_recursive(all_nodes, edit_nodes)
            child_res += child_values
        if res:
            res.update({"children": child_res})
            res = [res]
        else:
            res = child_res
        return res

    def _return_nodes_with_restriction(self):
        """
        The method to return nodes in recursion for that actual nodes. Not for all

        Args:
         * tooltip - bool

        Methods:
         * _return_nodes_recursive

        Returns:
         * list of folders dict with keys:
           ** id
           ** text - folder_name
           ** children - array with the same keys
        """
        nodes = self.search([
            ("id", "in", self.ids), "|", ("parent_id", "=", False), ("parent_id", "not in", self.ids),
        ])
        res = []
        for node in nodes:
            res += node._return_nodes_recursive_with_restrictions(all_nodes=SortedList(self.ids))
        return res

    def _return_nodes_recursive_with_restrictions(self, all_nodes=[]):
        """
        The method to go by all nodes recursively to prepare their list in js_tree format

        Methods:
         * action_js_format_folder_for_js_tree_web

        Args:
         * all_nodes - SortedList of ids of clouds.folder which are available for the current user

        Returns:
         * list of dicts (see action_js_format_folder_for_js_tree_web)

        Extra info:
         * we are under sudo to make sure all children are returned, but we show only those to which the current
           user has an access
         * Expected singleton
        """
        self = self.sudo()
        res = self.action_js_format_folder_for_js_tree_web(all_nodes) or {}
        child_res = []
        for child in self.child_ids:
            child_values = child._return_nodes_recursive_with_restrictions(all_nodes)
            child_res += child_values
        if res:
            res.update({"children": child_res})
            res = [res]
        else:
            res = child_res
        return res

    def _order_node_after_dnd(self, parent_id, position):
        """
        The method to normalize sequence when position of Node has been changed based on a new element position and
        its neighbours.
         1. In case of create we put element always to the end
         2. We try to update all previous elements sequences in case it become the same of a current one (sequence
            migth be negative)

        Args:
         * parent_id - int - id of node
         * position - int or false (needed to the case of create)

        Extra info:
         * Epected singleton
        """
        the_same_children_domain = [("id", "!=", self.id)]
        if parent_id:
            the_same_children_domain.append(("parent_id.id", "=", parent_id))
        else:
            the_same_children_domain.append(("parent_id", "=", False))
        this_parent_nodes = self.search(the_same_children_domain)
        if position is False:
            position = len(this_parent_nodes)
        if this_parent_nodes:
            neigbour_after = len(this_parent_nodes) > position and this_parent_nodes[position] or False
            neigbour_before = position > 0 and this_parent_nodes[position-1] or False
            sequence = False
            if neigbour_after:
                sequence = neigbour_after.sequence - 1
                # 1
                while neigbour_before and neigbour_before.sequence == sequence:
                    neigbour_before.sequence = neigbour_before.sequence - 1
                    position -= 1
                    neigbour_before = position > 0 and this_parent_nodes[position-1] or False
            elif neigbour_before:
                sequence = neigbour_before.sequence + 1
            if sequence is not False:
                self.sequence = sequence
