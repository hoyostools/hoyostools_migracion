/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { loadCSS, loadJS } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted, onPatched, onWillStart } = owl;


export class JsTreeWidget extends Component {
    static template = "cloud_base.jsTreeWidget";
    static props = { ...standardFieldProps };
    /*
    * Re-write to add services
    */
    setup() {
        this.dialogService = useService("dialog");
        onWillStart(async () => {
            const proms = [
                loadJS("/cloud_base/static/lib/jstree/jstree.min.js"),
                loadCSS("/cloud_base/static/lib/jstree/themes/default/style.css"),
            ]
            return Promise.all(proms);
        });
        onMounted(() => {
            this.jsTreeAnchor = $("#jsTreeContainer");
            this._renderJsTree();

        });
        onPatched(() => {
            this.jsTreeAnchor.jstree(true).settings.core.data = this.treeData;
            this.jsTreeAnchor.jstree(true).refresh();
        });
    }
    /*
    * Getter for tree data
    */
    get treeData() {
        return eval(this.props.record.data[this.props.name] || "[]")
    }
    /*
    * The method activate js tree based on the current value
    */
    _renderJsTree() {
        var self = this;
        const jsTree = this.jsTreeAnchor.jstree({
            "core" : {
                "check_callback" : function (operation, node, node_parent, node_position, more) {
                    if (operation === "move_node" && node_parent && node_parent.icon == "fa fa-file-o") {
                        // forbid assigning attachment node as parent
                        return false;
                    };
                    return true;
                },
                "data": self.treeData,
            },
            "plugins" : [
                "dnd",
                "state",
                "unique",
                "contextmenu",
            ],
            "contextmenu": {
                "items": function($node) {
                    const jsTreeAnchor = self.jsTreeAnchor.jstree(true);
                    return {
                        "Create": {
                            "label": _lt("Create"),
                            "action": function (obj) {
                                if ($node.icon == "fa fa-file-o") {
                                    self._onUploadFile(obj, jsTreeAnchor.get_node($node.parent));
                                }
                                else {
                                    $node = jsTreeAnchor.create_node($node);
                                    jsTreeAnchor.edit($node);
                                };
                            }
                        },
                        "Edit": {
                            "label": _lt("Edit"),
                            "action": function (obj) {
                                if ($node.icon == "fa fa-file-o") {
                                    self._onUploadFile(obj, jsTreeAnchor.get_node($node.parent), $node);
                                }
                                else {
                                    jsTreeAnchor.edit($node);
                                };
                            }
                        },
                        "Delete": {
                            "label": _lt("Delete"),
                            "action": function (obj) {
                                jsTreeAnchor.delete_node($node);
                            }
                        },
                        "Upload": {
                            "label": _lt("Upload File"),
                            "action": function (obj) {
                                if ($node.icon == "fa fa-file-o") {
                                    self._onUploadFile(obj, jsTreeAnchor.get_node($node.parent));
                                }
                                else {
                                    self._onUploadFile(obj);
                                };
                            }
                        },
                    }
                },
            },
        });
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        this.jsTreeAnchor.on("rename_node.jstree", self, function (event, data) {
            // when created, a node is always renamed
            self._onChangeTree(jsTreeAnchor);
        });
        this.jsTreeAnchor.on("move_node.jstree", self, function (event, data) {
            self._onChangeTree(jsTreeAnchor);
        });
        this.jsTreeAnchor.on("delete_node.jstree", self, function (event, data) {
            self._onChangeTree(jsTreeAnchor);
        });
        this.jsTreeAnchor.on("copy_node.jstree", self, function (event, data) {
            self._onChangeTree(jsTreeAnchor);
        });
    }
    /*
     * The method to add a new node
    */
    _onAddNode() {
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        var selectedNode = jsTreeAnchor.get_selected();
        selectedNode = jsTreeAnchor.create_node("#");
        if(selectedNode) { jsTreeAnchor.edit(selectedNode) };
    }
    /*
    * The method to add a new file node
    */
    _onUploadFile(data, $node, existing) {
        var self = this;
        const resID = existing ? parseInt(existing.id) : false;
        this.dialogService.add(FormViewDialog, {
            resModel: "ir.attachment",
            resId: resID,
            title: _lt("Upload attachment"),
            context: {"form_view_ref": "cloud_base.ir_attachment_view_form_simple_js_upload"},
            onRecordSaved: async (formRecord) => {
                const jsTreeAnchor = self.jsTreeAnchor.jstree(data.reference);
                const nodeObject = $node || jsTreeAnchor.get_node(data.reference);
                if (existing) {
                    jsTreeAnchor.set_text(existing, formRecord.data.name);
                    self._onChangeTree(jsTreeAnchor);
                }
                else {
                    const new_node_vals = {
                        "text": formRecord.data.name,
                        "icon": "fa fa-file-o",
                        "id": formRecord.data.id.toString(),
                    };
                    jsTreeAnchor.create_node(nodeObject || "#", new_node_vals, "last", function (new_node) {
                        jsTreeAnchor.open_node(nodeObject);
                        self._onChangeTree(jsTreeAnchor);
                    });
                };
            },
        });
    }
    /*
     * The method to apply changes
    */
    _onChangeTree(jsTreeAnchor) {
        const currentValue = JSON.stringify(jsTreeAnchor.get_json());
        this.props.record.update({ [this.props.name]: currentValue });
    }
};

export const jsTreeWidget = {
    component: JsTreeWidget,
    supportedTypes: ["char"],
};

registry.category("fields").add("jsTreeWidget", jsTreeWidget);


