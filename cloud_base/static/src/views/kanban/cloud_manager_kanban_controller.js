/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { Domain } from "@web/core/domain";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { useBus, useService } from "@web/core/utils/hooks";
const { useRef } = owl;


export class CloudManagerKanbanController extends KanbanController {
    /*
    * Re-write to add input upload
    */
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.uploadFileInputRef = useRef("uploadFileInput");
        this.uploadService = useService("file_upload");
        this.notification = useService("notification");
        this.actionService = useService("action");
        useBus(
            this.uploadService.bus,
            "FILE_UPLOAD_LOADED",
            () => { this.model.load() },
        );
    }
    /*
    * The method to process chosen files
    */
    async _onAddAttachment(ev) {
        if (!ev.target.files) {
            return this.notification.add(_lt("There have been no files selected!"), { type: "danger" });
        };
        if (!this.model.cloudsFolderId) {
            return this.notification.add(_lt("Please select a folder for uploaded files!"), { type: "danger" });
        };
        await this.uploadService.upload(
            "/cloud_base/upload_attachment",
            ev.target.files,
            {
                buildFormData: (formData) => { formData.append("clouds_folder_id", this.model.cloudsFolderId) },
                displayErrorNotification: true,
            },
        );
        ev.target.value = "";
    }
    /*
    * The method to add an URL attachment
    */
    async onClickAddUrl() {
        const kanbanModel = this.model;
        this.actionService.doAction(
            "cloud_base.add_url_attachment_action",
            {
                additionalContext: { default_folder_id: kanbanModel.cloudsFolderId },
                onClose: async() => {
                    await kanbanModel.root.load();
                    kanbanModel.notify();
                },
            },
        )
    }
    /*
    * The method to select all records that satisfy search criteria
    * It requires orm.call since not all records are shown on the view
    */
    async _onSelectAll() {
        const kanbanModel = this.model;
        var fullDomain = kanbanModel.env.searchModel.searchDomain;
        if (fullDomain.length != 0) {
            const selectedRecords = kanbanModel.selectedRecords.map((rec) => rec.id);
            fullDomain = Domain.or([fullDomain, [["id", "in", selectedRecords]]]).toList();
        }
        kanbanModel.selectedRecords = await this.orm.searchRead("ir.attachment", fullDomain, ["name"]);
        await kanbanModel.root.load();
        kanbanModel.notify();
    }
};

CloudManagerKanbanController.template = "cloud_base.CloudManagerKanbanView";
