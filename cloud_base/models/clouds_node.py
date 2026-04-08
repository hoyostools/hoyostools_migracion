# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class clouds_node(models.AbstractModel):
    """
    This is the Abstract Model to manage jstree nodes
    It is used for tags
    """
    _name = "clouds.node"
    _description = "Clouds Node"
    _rec_names_search = ["complete_name"]

    @api.depends("name", "parent_id.name")
    def _compute_display_name(self):
        """
        Overloading to reflect id and model name
        """
        for node in self:
            names = []
            current = node
            while current:
                names.append(current.name or "")
                current = current.parent_id
            node.display_name = " / ".join(reversed(names))

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for node in self:
            if node.parent_id:
                node.complete_name = "%s / %s" % (node.parent_id.complete_name, node.name)
            else:
                node.complete_name = node.name

    @api.constrains("parent_id")
    def _check_node_recursion(self):
        """
        Constraint for recursion
        """
        if not self._check_recursion():
            raise ValidationError(_("It is not allowed to make recursions!"))
        return True

    def _inverse_active(self):
        """
        Inverse method for active. There 2 goals:
         1. If a parent is not active, we activate it. It recursively activate all its further parents
         2. Deacticate all children. It will invoke deactivation recursively of all children after
        """
        for node in self:
            if node.active:
                # 1
                if node.parent_id and not node.parent_id.active:
                    node.parent_id.active = True
            else:
                # 2
                node.child_ids.write({"active": False})

    name = fields.Char(string="Name", required=True, translate=False)
    complete_name = fields.Char("Complete Name", compute="_compute_complete_name", store=True, recursive=True)
    description = fields.Html(string="Description", translate=False)
    active = fields.Boolean(string="Active", default=True, inverse=_inverse_active)
    sequence = fields.Integer(string="Sequence", default=0)

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        """
        Re-write to add "copy" in the title
        """
        if default is None:
            default = {}
        if not default.get("name"):
            default["name"] = _("%s (copy)") % (self.name)
        return super(clouds_node, self).copy(default)

    def action_js_format_for_js_tree(self):
        """
        The method to prepare dict for node

        Returns:
        * dict
        """
        res = {"text": self.name, "id": self.id}
        if self._name == "clouds.share":
            res.update({
                "data": {
                    "folder_ids": self.folder_ids.ids,
                    "tag_ids": self.tag_ids.ids,
                    "access_url": self.allow_by_token and self.acess_url or False,
                }
            })
        return res

    @api.model
    def action_get_hierarchy(self, res_model):
        """
        The method to prepare hierarchy

        Args:
         * res_model - string

        Methods:
         * _return_nodes

        Returns:
         * list
        """
        result = None
        user_group = res_model == "clouds.share" and "group_cloud_base_share" or "group_cloud_base_tags"
        if self.env.user.has_group("cloud_base." + user_group):
            result = self.env[res_model]._return_nodes()
        return result

    @api.model
    def action_create_node(self, model_name, data):
        """
        The method to force node unlinking

        Args:
         * key - string
         * data - dict of node params

        Methods:
         * update_node of password.node

        Returns:
         * dict
        """
        node_id = False
        if model_name:
            new_node = self.env[model_name].create_node(data)
            node_id = new_node.action_js_format_for_js_tree()
        return node_id

    @api.model
    def action_update_node(self, model_name, node_id, data, position):
        """
        The method to force node unlinking

        Args:
         * key - string
         * node_id - int - object ID
         * data - dict of node params
         * position - int or False

        Methods:
         * update_node of password.node

        Returns:
         * dict
        """
        res_id = False
        if model_name:
            node_object = self.env[model_name].browse(node_id)
            if node_object.exists():
                new_node = node_object.update_node(data, position)
                res_id = node_object.action_js_format_for_js_tree()
        return res_id

    @api.model
    def action_delete_node(self, model_name, node_id):
        """
        The method to force node unlinking

        Args:
         * key - string
         * node_id - int - object ID

        Methods:
         * delete_node of password.node
        """
        if model_name:
            node_object = self.env[model_name].browse(node_id)
            if node_object.exists():
                node_object.delete_node()

    @api.model
    def _return_nodes(self):
        """
        The method to return nodes in jstree format

        Methods:
         * _return_nodes_recursive

        Returns:
         * list of folders dict with keys:
           ** id
           ** text - folder_name
           ** children - array with the same keys
        """
        nodes = self.search([("parent_id", "=", False)])
        res = []
        for node in nodes:
            res.append(node._return_nodes_recursive())
        return res

    def _return_nodes_with_restriction(self):
        """
        The method to return nodes in recursion for that actual nodes. Not for all

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
            res.append(node._return_nodes_recursive(restrict_nodes=self))
        return res

    def _return_nodes_recursive(self, restrict_nodes=False):
        """
        The method to go by all nodes recursively to prepare their list in js_tree format

        Args:
         * restrict_nodes - node recordset

        Extra info:
         * sorted needed to fix unclear bug of zero-sequence element placed to the end
         * Expected singleton
        """
        res = self.action_js_format_for_js_tree()
        child_res = []
        child_ids = self.search([("id", "in", self.child_ids.ids)], order="sequence")
        for child in child_ids:
            if restrict_nodes and child not in restrict_nodes:
                continue
            child_res.append(child._return_nodes_recursive(restrict_nodes=restrict_nodes))
        res.update({"children": child_res})
        return res

    @api.model
    def create_node(self, data):
        """
        The method to update node name

        Methods:
         * _order_node_after_dnd

        Returns:
         * newly created record
        """
        name = data.get("text")
        parent_id = data.get("parent")
        if parent_id == "#":
            parent_id = False
        new_node_vals = {"name": name, "parent_id": parent_id}
        new_node = self.create([new_node_vals])
        new_node._order_node_after_dnd(parent_id=parent_id, position=False)
        return new_node

    def update_node(self, data, position):
        """
        The method to update node name

        Args:
         * data - dict of node params
         * position - false (in case it is rename) or int (in case it is move)

        Methods:
         * _order_node_after_dnd

        Returns:
         * udpated record

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
        return self

    def delete_node(self):
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
