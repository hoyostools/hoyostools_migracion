/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { makeEnv } from "@web/env";
import { mount } from "@odoo/owl";
import { PhotosSlideShow } from "@cloud_base/components/photos_slideshow/photos_slideshow";
import { templates } from "@web/core/assets";
import { useBus } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted, useState, xml } = owl;
import publicWidget from "@web/legacy/js/public/public_widget";


/*
* The method to get the current URL hash parameter
*/
function getParameterByName(parameter) {
    const currentUrl = window.location.href;
    parameter = parameter.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + parameter + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(currentUrl);
    if (!results) return "";
    if (!results[2]) return "";
    return decodeURIComponent(results[2].replace(/\+/g, " "));
};
/*
* The method to update the current param of the the URL
*/
function setParameterByName(currentLocation, parameter, parameterValue) {
    var url = currentLocation || window.location.href;
    const pattern = new RegExp("\\b(" + parameter + "=).*?(&|#|$)");
    if (url.search(pattern)>=0) {
        return url.replace(pattern,"$1" + parameterValue + "$2");
    };
    url = url.replace(/[?#]$/, "");
    return url + (url.indexOf("?")>0 ? "&" : "?") + parameter + "=" + parameterValue;
};
/*
* Jsreee component
*/
export class jsTreePortal extends Component {
    static props = {
        jstreeId: { type: String },
        shareInt: { type: String },
        shareToken: { type: String },
        selectedFolder: { type: String },
        rpc_service: { type: Function },
    };
    /*
    * Overwrite to save the initinal state
    */
    setup() {
        this.state = useState({
            treeData: null,
            allowCreate: null,
            allowSearch: null,
        });
        this.searchString = "";
        this.lastSearch = false;
        onWillStart(async () => {
            await this._loadSettings(this.props);
            await this._loadTreeData(this.props);
        });
        onMounted(() => {
            this.jsTreeAnchor = $("#"+this.id);
            this.jsTreeSearchInput = $("#jstr_input_" + this.id)[0];
            this._renderJsTree();
        })
    }
    /*
    * Getter for id (jstree_key unique reference)
    */
    get id() {
        return this.props.jstreeId;
    }
    /*
    * Getter for the title
    */
    get title() {
        return this.id == "cb-folders" ? _lt("Folders") : _lt("Tags");
    }
    /*
    * Getter for parameter (URL query for the object)
    */
    get parameter() {
        return this.id == "cb-folders" ? "folders" : "tags";
    }
    /*
    * Getter for resModel
    */
    get resModel() {
        return this.id == "cb-folders" ? "clouds.folder" : "clouds.tag";
    }
    /*
    * The method to get basic jstree settings
    */
    async _loadSettings(props) {
        const jstreeSettings = await this.props.rpc_service(this.getRPCRoute("get_setting", this.resModel), []);
        Object.assign(this.state, {
            allowCreate: jstreeSettings.allow_create,
            allowSearch: jstreeSettings.allow_search,
        });
    }
    /*
    * The method to get jsTree data
    */
    async _loadTreeData(props) {
        const jstreeData = await this.props.rpc_service(this.getRPCRoute("get_nodes", this.resModel), []);
        Object.assign(this.state, { treeData: jstreeData });
    }
    /*
    * The method to prepare the RPC url
    */
    getRPCRoute(targetUrl, targetParam=null) {
        let targetHref = "/clouds/share/" + targetUrl + "/" + this.props.shareInt;
        if (targetParam) {
            targetHref += "/" + targetParam
        };
        if (this.props.shareToken) {
            targetHref += "/token/" + this.props.shareToken
        };
        return targetHref;
    }
    /*
    * The method to highlight not selected parent nodes that have selected children
    * That's triggered when a node is selected or opened. The reason for the latter is that not loaded nodes get
    * class from state while we do not want to always iterate over those
    */
    _highlightParentCloud(jsTreeAnchor, checkedNodes, jsSelector) {
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
    /*
    * The method to highlight selected folder
    */
    _highlightSelectedFolder(jsSelector) {
        if (this.id == "cb-folders") {
            $(jsSelector+ " a#" + this.props.selectedFolder +"_anchor").addClass("jstree-clicked");
        };
    }
    /*
    * The method to prepare context meny
    */
    getContextMenu() {
        var self = this;
        return {
            "select_node": false,
            "items": function($node) {
                const jsTreeAnchor = self.jsTreeAnchor.jstree(true);
                var actions = {
                    "downloadZip": {
                        "label": _lt("Download as archive"),
                        "action": function (obj) {
                            window.location = self.getRPCRoute("upload", self.resModel + "/" + $node.id);
                        }
                    },
                };
                if (self.state.allowCreate) {
                    Object.assign(actions, {
                        "Create": {
                            "label": _lt("Create"),
                            "action": function (obj) {
                                $node = jsTreeAnchor.create_node($node);
                                jsTreeAnchor.edit($node);
                            }
                        }
                    })
                };
                return actions
            },
        };
    }
    /*
    * The method to initiate jstree
    */
    async _renderJsTree() {
        const self = this;
        self.jsTreeAnchor.jstree("destroy");
        const jsTreeOptions = {
            "core" : {
                "themes": { "icons": false },
                "check_callback" : true,
                "data": this.state.treeData,
                "multiple" : true,
            },
            "plugins" : ["checkbox", "contextmenu", "state", "search"],
            "state" : { "key" : self.id },
            "checkbox" : { "three_state" : false, "cascade": "down", "tie_selection" : false },
            "contextmenu": this.getContextMenu(),
        };
        const jsTree = this.jsTreeAnchor.jstree(jsTreeOptions);
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        const checkedItemsIds = getParameterByName(self.parameter).split(",");
        if (this.state.allowCreate) {
            this.jsTreeAnchor.on("rename_node.jstree", self, async function (event, data) {
                const newNodeId = await self.props.rpc_service(
                    self.getRPCRoute("create", self.resModel), { data: data.node }
                );
                window.location.reload()
            });
        };
        this.jsTreeAnchor.on("state_ready.jstree", self, function (event, data) {
            jsTreeAnchor.check_node(checkedItemsIds);
            const itemsDifferent = jsTreeAnchor.get_checked().filter(x => checkedItemsIds.indexOf(x) < 0);
            jsTreeAnchor.uncheck_node(itemsDifferent);
            self._highlightParentCloud(jsTreeAnchor, checkedItemsIds, "#" + self.id);
            self._highlightSelectedFolder("#" + self.id);
            self.jsTreeAnchor.on("check_node.jstree uncheck_node.jstree", self, function (event, data) {
                if (self.id == "cb-folders") {
                    self.reloadTreeCloudSearch(jsTreeAnchor);
                }
                else {
                    self.reloadTreeCloudSearch(jsTreeAnchor);
                };
            });
            self.jsTreeAnchor.on("open_node.jstree", self, function (event, data) {
                // On each opening we should recalculate highlighted parents and tooltips
                self._highlightParentCloud(jsTreeAnchor, checkedItemsIds, "#" + self.id);
                self._highlightSelectedFolder();
            });
            self.jsTreeAnchor.on("search.jstree", self, function (event, data) {
                if (data.res.length != 0) {
                    self.lastSearch = data.res[0];
                };
            });
            self.jsTreeAnchor.on("clear_search.jstree", self, function (event, data) {
                self.lastSearch = false;
            });
        });
    }
    /*
    * The method to apply page reloading based on JsTree checks
    */
    reloadTreeCloudSearch(jstreeAnchor) {
        var currentLocation = window.location.href;
        var selectedFolder = this.props.selectedFolder || false;
        const checkedItems = jstreeAnchor.get_checked();
        const currentItemsStr = getParameterByName(this.parameter);
        var checkedItemsStr = "";
        if (checkedItems.length != 0) {
            checkedItemsStr = checkedItems.join(",");
            if (!checkedItemsStr) { checkedItemsStr = "" };
        };
        if (selectedFolder) {
            if (!checkedItems || checkedItems.length == 0) {
                // no checked items
                selectedFolder = "";
            }
            else if (!checkedItems.includes(selectedFolder)) {
                // selected folder is not checked (for example, it is unchecked) => get the first found
                selectedFolder = checkedItems[0]
            };
            if (selectedFolder != getParameterByName("selected_folder")) {
                currentLocation = setParameterByName(currentLocation, "selected_folder", selectedFolder);
            };
        };
        if (currentItemsStr != checkedItemsStr) {
            currentLocation = setParameterByName(currentLocation, this.parameter, checkedItemsStr);
        };
        if (currentLocation != window.location) {
            window.location = currentLocation;
        };
    };
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
        if (this.searchString) {
            this.jsTreeAnchor.jstree("search", this.searchString)
        }
        else {
            this.jsTreeAnchor.jstree("clear_search")
        };
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
    * The method to uncheck all nodes in the tree
    */
    _onClearJsTree() {
        const jsTreeAnchor = this.jsTreeAnchor.jstree(true);
        jsTreeAnchor.uncheck_all();
        jsTreeAnchor.save_state();
        this.reloadTreeCloudSearch(jsTreeAnchor);
    }
}
jsTreePortal.template = xml`<t>
    <t t-if="state.treeData and state.treeData.length">
        <b t-out="title"/> <small><i class="fa fa-ban cb-button ml4 text-muted" t-on-click.prevent="() => this._onClearJsTree()"></i></small>
        <div class="jstr-panel-body w-100">
            <div t-if="state.allowSearch" class="jstr-search-row">
                <div class="jstr-search-view">
                    <i class="fa fa-search jstr-search-icon jstr-search-icon-search" t-on-click="() => this._onSearchExecute()"/>
                    <i class="fa fa-ban jstr-search-icon jstr-search-icon-trash" t-on-click="() => this._onSearchClear()"/>
                    <div class="jstr-search-input-container">
                        <input t-attf-id="jstr_input_#{id}" placeholder="search" t-on-change="(event) => this._onSearchChange(event)" t-on-keyup="(event) => this._onSearchkeyUp(event)"/>
                    </div>
                </div>
            </div>
            <div t-att-id="id">
            </div>
        </div>
    </t>
</t>`;
/*
* Initiate the widgets on the articles' overview
*/
publicWidget.registry.cloudBasePortal = publicWidget.Widget.extend({
    selector: ".cb-overview",
    jsLibs: ["/cloud_base/static/lib/jstree/jstree.min.js"],
    cssLibs: ["/cloud_base/static/lib/jstree/themes/default/style.css"],
    events: {
        "dragenter #cb-attachments-container": "_onDragEnter",
        "dragleave .o_cloud_drop_area": "_onDragLeave",
        "drop.prevent .o_cloud_drop_area": "_onDrop",
        "dragover .o_cloud_drop_area": "_onDragOver",
        "click #start-slideshow": "_onStartSlideshow",
    },
    /*
    * Re-write to bind services
    */
    init: function (parent, obj, placeholder) {
        this._super.apply(this, arguments);
        this.rpc_service = this.bindService("rpc");
        this.uploadService = this.bindService("file_upload");
        this.uploadService.bus.addEventListener("FILE_UPLOAD_LOADED", () => {
            if (this.reloadNeeded) {
                this.reloadNeeded = false;
                window.location.reload();
            }
        });
    },
    /*
    * Initialize jstrees components
    */
    async start() {
        this.shareInt = $(".cb-share_id")[0].id;
        this.shareToken = $(".cb-sharetoken")[0].id;
        this.selectedFolder = $(".cb-selected-folder")[0].id;
        this.allowAddFolders = $(".allow-add-folders")[0].id == "1";
        this.attachmentsDomain = $(".attachments-domain")[0].id;
        const env = makeEnv();
        const props = {
            rpc_service: this.rpc_service.bind(this),
            shareInt: this.shareInt,
            shareToken: this.shareToken,
            selectedFolder: this.selectedFolder,
        };
        const folderLocation = $("#cb-folders-container");
        if (folderLocation && folderLocation.length) {
            props.jstreeId = "cb-folders";
            await mount(jsTreePortal, folderLocation[0], { env, templates, props });
        };
        const tagLocation = $("#cb-tags-container");
        if (tagLocation && tagLocation.length) {
            props.jstreeId = "cb-tags";
            await mount(jsTreePortal, tagLocation[0], { env, templates, props });
        };
    },
    /*
    * The event to make the dropzone visible
    */
    _onDragEnter(event) {
        $(".o_cloud_drop_area").removeClass("cb-hidden");
    },
    /*
    * The event to hover d&d. Needed to make possible _onDrop
    */
    _onDragOver(event) {
        event.preventDefault();
    },
    /*
    * The event to hide dropzone
    */
    _onDragLeave(event) {
        $(".o_cloud_drop_area").addClass("cb-hidden");
    },
    /*
    * The event to upload files by d&d
    * Folders drop is supported only for the part of browsers that have getAsFileSystemHandle
    */
    async _onDrop(ev) {
        ev.preventDefault();
        let uploadInput = $("#cb-files-input")[0];
        let files = ev.originalEvent.dataTransfer ? ev.originalEvent.dataTransfer.files : false;
        if (uploadInput && !!files) {
            let items = [...ev.originalEvent.dataTransfer.items];
            if (this.allowAddFolders && typeof(items[0].getAsFileSystemHandle) != "undefined") {
                await this._onManageFiles([...ev.originalEvent.dataTransfer.items]);
                if (!this.reloadNeeded) {
                    window.location.reload();
                };
            }
            else {
                uploadInput.files = ev.originalEvent.dataTransfer.files;
                uploadInput.dispatchEvent(new Event("change"));
                $(".o_cloud_drop_area").addClass("cb-hidden");
            };
        };
    },
    /*
    * The method to mount slideshow event for the all found images
    */
    async _onStartSlideshow(event) {
        var rpcRoute = "/clouds/share/slideshow/" + this.shareInt;
        if (this.shareToken) {
            rpcRoute += "/token/" + this.shareToken;
        };
        const attachments = await this.rpc_service(
            rpcRoute, { attachments_domain: this.attachmentsDomain}
        );
        const env = makeEnv();
        const props = { images: attachments };
        await mount(PhotosSlideShow, $("body")[0], { env, templates, props });
    },
    /*
    * The method to prepare a file for upload for the folder
    */
    async uploadFile(handle, currentFolder, filesDict) {
        this.reloadNeeded = true;
        let file = await handle.getFile();
        if (filesDict[currentFolder]) {
            filesDict[currentFolder].push(file);
        }
        else {
            filesDict[currentFolder] = [file];
        }
        return filesDict
    },
    /*
    * The method to add a folder
    */
    async createFolder(handle, currentFolder) {
        var rpcRoute = "/clouds/share/create/" + this.shareInt + "/clouds.folder";
        if (this.shareToken) {
            rpcRoute += "/token/" + this.shareToken;
        };
        const newFolderId = await this.rpc_service(
            rpcRoute, { data: {"text": handle.name, "parent": currentFolder}}
        );
        return newFolderId
    },
    /*
    * The method to get folders and files
    */
    async _onManageFiles(files) {
        const fileHandles = files.filter((item) => item.kind === "file").map((item) => item.getAsFileSystemHandle());
        let filesDict = {};
        for await (const handle of fileHandles) {
            if (handle.kind === "directory") {
                filesDict = await this._onManageFilesRecursively(handle, [handle.name], this.selectedFolder, filesDict);
            }
            else {
                filesDict = await this.uploadFile(handle, this.selectedFolder, filesDict);
            };
        };
        var rpcRoute = "/clouds/share/add/" + this.shareInt;
        if (this.shareToken) {
            rpcRoute += "/token/" + this.shareToken;
        };
        for await (const [folderKey, filesArray] of Object.entries(filesDict)) {
            const res = await this.uploadService.upload(rpcRoute+"?selected_folder=" + folderKey + "&noredirect=1", filesArray);
        };
    },
    /*
    * The recursive method to read files and folders and create those in Odoo
    */
    async _onManageFilesRecursively(entry, path, currentFolder, filesDict) {
        if (entry.kind === "file") {
            filesDict = await this.uploadFile(entry, currentFolder, filesDict);
        }
        else if (entry.kind === "directory") {
            const newFolderId = await this.createFolder(entry, currentFolder);
            let index = 0;
            for await (const handle of entry.values()) {
                path.push(handle.name);
                let newPath = path.map((p) => p);
                filesDict = await this._onManageFilesRecursively(handle, newPath, newFolderId, filesDict);
                path.pop();
            };
        };
        return filesDict;
    },
});
