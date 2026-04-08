/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Component, useState } from "@odoo/owl";
import { useBus, useService } from "@web/core/utils/hooks";


export class CloudDropZone extends Component {
    static props = {
        visible: { type: Boolean, optional: true },
        hideZone: { type: Function, optional: true },
        kanbanModel: { type: Object },
        kanbanRenderer: { type: Object },
    };
    static defaultProps = { hideZone: () => {} };
    static template = "cloud_base.CloudDropZone";
    /*
    * Re-write to have notification services
    */
    setup() {
        this.notificationService = useService("notification");
        this.orm = useService("orm");
        this.uploadService = useService("file_upload");
        useBus(
            this.uploadService.bus,
            "FILE_UPLOAD_LOADED",
            () => {  this.props.kanbanModel.load() },
        );
    }
    /*
    * The method to finalize file upload
    * Folders drop is supported only for the part of browsers that have getAsFileSystemHandle
    */
    async onDrop(ev) {
        const selector = ".o_input_file";
        let uploadInput = ev.target.closest(".o_cloud_drop_area").parentElement.querySelector(selector) || document.querySelector(selector);
        let files = ev.dataTransfer ? ev.dataTransfer.files : false;
        if (uploadInput && !!files && this.props.kanbanModel.cloudsFolderId) {
            let items = [...ev.dataTransfer.items];
            if (typeof(items[0].getAsFileSystemHandle) != "undefined") {
                await this._onManageFiles(items);
            }
            else {
                uploadInput.files = ev.dataTransfer.files;
                uploadInput.dispatchEvent(new Event("change"));
            };
        }
        else {
            this.notificationService.add(_t("Could not upload files"), { type: "danger" });
        };
        this.props.hideZone();
    }
    /*
    * The method to prepare a file for upload for the folder
    */
    async uploadFile(handle, currentFolder, filesDict) {
        let file = await handle.getFile();
        if (filesDict[currentFolder]) {
            filesDict[currentFolder].push(file);
        }
        else {
            filesDict[currentFolder] = [file];
        }
        return filesDict
    }
    /*
    * The method to add a folder
    */
    async createFolder(handle, currentFolder) {
        this.reloadNeeded = true;
        const newFolderIds = await this.orm.create("clouds.folder", [{
            "name": handle.name, "parent_id": currentFolder,
        }]);
        return newFolderIds[0]
    }
    /*
    * The method to get folders and files
    */
    async _onManageFiles(files) {
        const fileHandles = files.filter((item) => item.kind === "file").map((item) => item.getAsFileSystemHandle());
        let filesDict = {};
        for await (const handle of fileHandles) {
            if (handle.kind === "directory") {
                filesDict = await this._onManageFilesRecursively(handle, [handle.name], this.props.kanbanModel.cloudsFolderId, filesDict);
            }
            else {
                filesDict = await this.uploadFile(handle, this.props.kanbanModel.cloudsFolderId, filesDict)
            };
        };
        for await (const [folderKey, filesArray] of Object.entries(filesDict)) {
            await this.uploadService.upload(
                "/cloud_base/upload_attachment",
                filesArray,
                {
                    buildFormData: (formData) => { formData.append("clouds_folder_id", folderKey) },
                    displayErrorNotification: true,
                },
            );
        };
        if (this.reloadNeeded) {
            this.props.kanbanRenderer._reloadNavigation();
            this.reloadNeeded = false;
        };
    }
    /*
    * The recursive method to read files and folders and create those in Odoo
    */
    async _onManageFilesRecursively(entry, path, currentFolder, filesDict) {
        if (entry.kind === "file") {
            filesDict = await this.uploadFile(entry, currentFolder, filesDict);
        }
        else if (entry.kind === "directory") {
            const newFolderId = await this.createFolder(entry, currentFolder);
            for await (const handle of entry.values()) {
                path.push(handle.name);
                let newPath = path.map((p) => p);
                filesDict = await this._onManageFilesRecursively(handle, newPath, newFolderId, filesDict);
                path.pop();
            }
        };
        return filesDict
    }
};
