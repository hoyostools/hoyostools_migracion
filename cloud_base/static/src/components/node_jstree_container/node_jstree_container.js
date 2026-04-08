/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { Domain } from "@web/core/domain";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { Tooltip } from "@web/core/tooltip/tooltip";
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted, useState } = owl;
const componentModel = "clouds.node";
const jsTreemodels = { "tags": "clouds.tag", "shares": "clouds.share" };


export class NodeJsTreeContainer extends Component {
    static template = "cloud_base.NodeJsTreeContainer";
    static props = {
        jstreeTitle: { type: String },
        jstreeId: { type: String },
        onUpdateSearch: { type: Function },
        kanbanModel: { type: Object },
    };
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.state = useState({ treeData: null });
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.dialogService = useService("dialog");
        this.popover = useService("popover");
        this.searchString = "";
        onWillStart(async () => {
            await this._loadTreeData(this.props);
        });
        onMounted(() => {
            this.jsTreeAnchor = $("#"+this.id);
            this.jsTreeSearchInput = $("#jstr_input_" + this.id)[0];
            this._renderJsTree();
        })
    }
    /*
    * Getter for title
    */
    get title() {
        return this.props.jstreeTitle;
    }
    /*
    * Getter for id (jstree_key unique reference)
    */
    get id() {
        return this.props.jstreeId;
    }
    /*
    * The method to update jsTree data
    */
    async _loadTreeData() {
        const jstreeData = await this.orm.call(componentModel, "action_get_hierarchy", [jsTreemodels[this.id]]);
        Object.assign(this.state, { treeData: jstreeData });
    }
    /*
    * The method to get context_menu options
    */
    _getJsTreeContextMenu() {
        var self = this;
        return {
            "select_node": false,
            "items": function($node) {
                const jsTreeAnchor = self.jsTreeAnchor.jstree(true);
                const items = {};
                items.downloadZip = {
                    "label": _lt("Download as archive"),
                    "action": function (obj) {
                        if (self.id == "tags") {
                            window.location = "/cloud_base/tag_upload/" + $node.id;
                        }
                        else if (self.id == "shares") {
                            window.location = "/cloud_base/share_upload/" + $node.id;
                        }
                    }
                };
                if (self.id == "shares") {
                    items.sendInvitataion = {
                        "label": _lt("Send Invitation"),
                        "action": function (obj) {
                            if ($node.data && $node.id) {
                                self.actionService.doAction(
                                    "cloud_base.share_send_invitation_action",
                                    { "additionalContext": { "default_share_id": parseInt($node.id) } }
                                );
                            };
                        },
                        "separator_before": true,
                    };
                    if ($node.data && $node.data.access_url) {
                        items.copyClouds = {
                            "label": _lt("Copy access url"),
                            "action": function (obj) {
                                if ($node.data && $node.data.access_url) {
                                    var popoverTooltip = _lt("Successfully copied!"),
                                        popoverClass = "text-success",
                                        popoverTimer = 800;
                                    try {
                                        browser.navigator.clipboard.writeText($node.data.access_url);
                                    }
                                    catch {
                                        popoverTooltip = _lt("Error! This browser doesn't allow to copy to clipboard");
                                        popoverClass = "text-danger";
                                        popoverTimer = 2500;
                                    };
                                    const popoverElement = $("#shares a#"+$node.a_attr.id);
                                    if (popoverElement && popoverElement.length != 0) {
                                        const closeTooltip = self.popover.add(
                                            popoverElement[0], Tooltip, { tooltip: popoverTooltip }, { popoverClass: popoverClass },
                                        );
                                        browser.setTimeout(() => { closeTooltip() }, popoverTimer);
                                    };
                                };
                            },
                        };
                    };
                    items.openInClouds = {
                        "label": _lt("Preview portal"),
                        "action": function (obj) {
                            if ($node.data && $node.id) {
                                window.open("/clouds/share/" + $node.id, "_blank").focus();
                            };
                        }
                    };
                };
                items.Create = {
                    "label": _lt("Create"),
                    "action": function (obj) {
                        $node = jsTreeAnchor.create_node($node);
                        jsTreeAnchor.edit($node);
                    },
                    "separator_before": true,
                };
                items.Rename = {
                    "label": _lt("Rename"),
                    "action": function (obj) { jsTreeAnchor.edit($node) },
                };
                items.Edit = {
                    "label": _lt("Edit"),
                    "action": function (obj) { self._onEditNodeForm(jsTreeAnchor, $node) },
                };
                items.Remove = {
                    "separator_before": false,
                    "separator_after": false,
                    "label": _lt("Archive"),
                    "action": function (obj) { jsTreeAnchor.delete_node($node) },
                };
                return items
            },
        };
    }
    /*
    * The method to initiate jstree
    */
    async _renderJsTree() {
        if (!this.state.treeData) {
            return;
        };
        var self = this;
        const contextMenu = this._getJsTreeContextMenu();
        const plugins = ["checkbox", "contextmenu", "search", "state", "dnd"];
        const jsTreeOptions = {
            "core" : {
                "check_callback" : function (operation, node, node_parent, node_position, more) {
                    if (operation === "move_node") {
                        if (node.icon == "attachment_update" && (!node_parent || node_parent.id == "#")) {
                            return false
                        };
                    };
                    return true
                },
                "themes": {"icons": false},
                "data": this.state.treeData,
                "multiple" : true,
            },
            "plugins" : plugins,
            "state" : { "key" : this.id },
            "checkbox" : {
                "three_state" : false,
                "cascade": "down",
                "tie_selection" : false,
            },
            "contextmenu": contextMenu,
        };
        const jsTree = this.jsTreeAnchor.jstree(jsTreeOptions);
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        this.jsTreeAnchor.on("rename_node.jstree", self, function (event, data) {
            // This also includes "create" event. Since each time created, a node is updated then
            self._onUpdateNode(jsTreeAnchor, data, false);
        });
        this.jsTreeAnchor.on("move_node.jstree", self, function (event, data) {
            self._onUpdateNode(jsTreeAnchor, data, true);
        });
        this.jsTreeAnchor.on("delete_node.jstree", self, function (event, data) {
            self._onDeleteNode(data);
        });
        this.jsTreeAnchor.on("copy_node.jstree", self, function (event, data) {
            self._onUpdateNode(jsTreeAnchor, data, true);
        });
        this.jsTreeAnchor.on("state_ready.jstree", self, function (event, data) {
            self._onUpdateDomain(jsTreeAnchor);
            self.jsTreeAnchor.on("check_node.jstree uncheck_node.jstree", self, function (event, data) {
                // We register "checks" only after restoring the tree to avoid multiple checked events
                self._onUpdateDomain(jsTreeAnchor);
            })
            self.jsTreeAnchor.on("open_node.jstree", self, function (event, data) {
                // On each opening we should recalculate highlighted parents
                self._highlightParent(jsTreeAnchor, jsTreeAnchor.get_checked(), "#"+self.id);
            })
        });
    }
    /*
    * The method to calculate domain based on checks and trigger the parent search model to reload
    * For shares we get full data over checked items to retrieve its custom data (folders&tags)
    */
    _onUpdateDomain(jsTreeAnchor) {
        const checkedTreeItems = jsTreeAnchor.get_checked(this.id == "shares");
        this._highlightParent(jsTreeAnchor, checkedTreeItems, "#"+this.id);
        this.props.onUpdateSearch(this.id, this._getDomain(checkedTreeItems));
    }
    /*
    * The method to uncheck all nodes in the tree
    */
    _onClearJsTree() {
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        jsTreeAnchor.uncheck_all();
        jsTreeAnchor.save_state();
        this._onUpdateDomain(jsTreeAnchor);
    }
    /*
    * The method to get change in the search input and save it
    */
    _onSearchChange(event) {
        this.searchString = event.currentTarget.value;
    }
    /*
    * The method to execute search in jsTree
    */
    _onSearchExecute() {
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        jsTreeAnchor.uncheck_all();
        if (this.searchString) {
            this.jsTreeAnchor.jstree("search", this.searchString);
        }
        else {
            this.jsTreeAnchor.jstree("clear_search");
        };
        this._onUpdateDomain(jsTreeAnchor); // so unchecked leaves are reflected
    }
    /*
     * The method to manage keyup on search input > if enter then make search
    */
    _onSearchkeyUp(event) {
        if (event.keyCode === 13) {
            this._onSearchExecute();
        };
    }
    /*
     * The method to clear seach input and clear jstree search
    */
    _onSearchClear() {
        this.jsTreeSearchInput.value = "";
        this.searchString = "";
        this.jsTreeAnchor.jstree("clear_search");
    }
    /*
     * The method to trigger update of jstree node
    */
    async _onUpdateNode(jsTreeAnchor, data, position) {
        if (data.node && data.node.icon && data.node.icon === "attachment_update") {
            // this only attachments drag&drop
            await this.orm.call(
                jsTreemodels[this.id], "action_update_attachment", [[parseInt(data.node.parent)], data.node.id],
            );
            this.jsTreeAnchor.jstree(true).delete_node(data.node);
            await this._onUpdateDomain(jsTreeAnchor);
            return true
        };
        var newNodeId;
        if (data.node.id === parseInt(data.node.id).toString()) {
            // node exists in tree (no need for refreshing)
            if (position) {
                // that a node move
                position = parseInt(data.position);
            };
            newNodeId = await this.orm.call(
                componentModel,
                "action_update_node",
                [jsTreemodels[this.id], parseInt(data.node.id), data.node, position],
            );
        }
        else {
            // brand new node
            newNodeId = await this.orm.call(
                componentModel,
                "action_create_node",
                [jsTreemodels[this.id], data.node],
            );
        }
        this._refreshNodeAfterUpdate(data.node, newNodeId);
    }
    /*
     * The method to trigger unlink of jstree node
    */
    async _onDeleteNode(data) {
        if (data.node.icon === "attachment_update") {
            return
        };
        await this.orm.call(componentModel, "action_delete_node", [jsTreemodels[this.id], parseInt(data.node.id)]);
    }
    /*
     * The method to add a new root jstree item
    */
    _onAddRootTag() {
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        var selectedNode = jsTreeAnchor.get_selected();
        selectedNode = jsTreeAnchor.create_node("#");
        if(selectedNode) { jsTreeAnchor.edit(selectedNode) };
    }
    /*
     * The method to open node edit form
    */
    async _onEditNodeForm(jsTreeAnchor, node) {
        var self = this;
        this.dialogService.add(FormViewDialog, {
            resModel: jsTreemodels[this.id],
            resId: parseInt(node.id),
            context: {},
            title: _lt("Settings"),
            preventCreate: false,
            preventEdit: false,
            onRecordSaved: async (formRecord) => {
                jsTreeAnchor.set_text(node, formRecord.data.name);
                if (formRecord.data.parent_id && formRecord.data.parent_id.length != 0) {
                    const newParent = formRecord.data.parent_id[0].toString();
                    if (newParent != node.parent) {
                        jsTreeAnchor.move_node(node, newParent);
                    };
                };
                const newNodeId = await self.orm.call(
                    jsTreemodels[this.id], "action_js_format_for_js_tree", [[parseInt(node.id)]],
                );
                self._refreshNodeAfterUpdate(node, newNodeId)
            },
        });
    }
    /*
     * The method to refresh updated node
    */
    _refreshNodeAfterUpdate(node, new_data) {
        if (!new_data) {
            return
        };
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        jsTreeAnchor.set_id(node, new_data.id);
        jsTreeAnchor.set_text(node, new_data.text);
        node.data = new_data.data;
    }
    /*
    * The method to calculate domain based on JsTree values
    */
    _getDomain(checkedTreeItems) {
        if (this.id == "tags") {
            return this._getMany2ManyDomain(checkedTreeItems, "cloud_tag_ids")
        }
        else if (this.id == "shares") {
            const shares = checkedTreeItems.map((record) => record.id);
            const folders = checkedTreeItems.map((record) => record.data.folder_ids).flat();
            const tags = checkedTreeItems.map((record) => record.data.tag_ids).flat();
            const sharesDomain = this._getMany2ManyDomain(shares, "share_ids");
            const foldersDomain = this._getMany2OneDomain(folders, "clouds_folder_id");;
            const tagsDomain = this._getMany2ManyDomain(tags, "cloud_tag_ids");;
            const domain = Domain.or([sharesDomain, foldersDomain, tagsDomain]).toList();
            return domain;
        };
        return []
    }
    /*
    * The method to prepare the domain for M2O 'in' domain
    */
    _getMany2OneDomain(checkedTreeItems, field) {
        if (checkedTreeItems.length != 0) {
            return [[field, "in", checkedTreeItems]];
        };
        return [];
    }
    /*
    * The method to prepare the domain for M2M 'in' domain
    */
    _getMany2ManyDomain(checkedTreeItems, field) {
        var domain = [];
        checkedTreeItems.forEach(function (checkedItem) {
            domain = Domain.or([domain, [[field, "in", parseInt(checkedItem)]]]).toList();
        });
        return domain;
    }
    /*
    * The method to highlight not selected parent nodes that have selected children
    * That's triggered when a node is selected or opened. The reason for the latter is that not loaded nodes get
    * class from state while we do not want to always iterate over those
    */
    _highlightParent(jsTreeAnchor, checkedNodes, jsSelector) {
        $(jsSelector + "* .jstr-selected-parent").removeClass("jstr-selected-parent");
        var allParentNodes = [];
        checkedNodes.forEach(function (node) {
            const thisNodeParents = jsTreeAnchor.get_path(node, false, true);
            allParentNodes = allParentNodes.concat(thisNodeParents);
        });
        allParentNodes = [... new Set(allParentNodes)];
        allParentNodes.forEach(function (nodeID) {
            $(jsSelector + " * .jstree-node#" + nodeID).addClass("jstr-selected-parent");
        });
    }
};
