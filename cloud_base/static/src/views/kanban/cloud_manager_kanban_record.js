/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { KanbanRecord } from "@web/views/kanban/kanban_record";
import { useFileViewer } from "@web/core/file_viewer/file_viewer_hook";
import { useService } from "@web/core/utils/hooks";

const notGlobalActions = ["a", ".dropdown", ".oe_kanban_action"].join(",");


export class CloudManagerKanbanRecord extends KanbanRecord {
    setup() {
        super.setup();
        this.store = useService("mail.store");
        this.fileViewer = useFileViewer();
    }
    /*
    * Re-write to add its own classes for selected kanban record
    */
    getRecordClasses() {
        let result = super.getRecordClasses();
        if (this.props.record.selected) {
            result += " jstr-kanban-selected";
        };
        return result;
    }
    /*
    * The method to make mail attachment model
    */
    getMailAttachment(recordItem) {
        const attachment = this.store.Attachment.insert({
            id: recordItem.data.id,
            filename: recordItem.data.name,
            name: recordItem.data.name,
            mimetype: recordItem.data.mimetype,
            cloudSynced: recordItem.data.cloud_key ? true : false,
            cloudURL: recordItem.data.url,
        });
        return attachment
    }
    /*
    * The method to manage clicks on kanban record
    */
    onGlobalClick(ev) {
        if (ev.target.closest(notGlobalActions)) {
            // A real action or button is clicked --> need to proceed that
            return;
        }
        else if (ev.target.closest(".o_kanban_image")) {
            // An image is clicked --> preview is opened
            const thisPageAttachments = this.props.record.model.root.records.map((item) => this.getMailAttachment(item))
            const attachment = this.getMailAttachment(this.props.record)
            this.fileViewer.open(attachment, thisPageAttachments)
        }
        else {
            // Others clicks --> add to selection/remove from selection
            this.props.record.onRecordClick(ev, {});
        };
    }
    /*
    * The method to get a record to change its folder or tags by dropping it to the left panel
    */
    onDragStart(event) {
        event.preventDefault(); // to avoid standard drag&drop
        event.dataTransfer.effectAllowed = "move"; // distinguish file dragging and attachments change
        if (!this.props.record.selected) {
            this.props.record.toggleSelection(true); // before moving, a record should be added to the selection
        };
        const selectedRecords = this.props.record.model.selectedRecords.map(function(record) {
            return { id: "attachment_" + record.id, text: record.name, icon: "attachment_update" }
        });
        const draggableElement = document.createElement("div");
        draggableElement.classList.add("jstree-default");
        draggableElement.id = "jstree-dnd";
        const draggableIcon = document.createElement("i");
        draggableIcon.classList.add("jstree-icon", "jstree-er");
        $(draggableIcon).appendTo(draggableElement);
        const dragText = selectedRecords.length == 1 ? selectedRecords[0].text : selectedRecords.length + _t(" attacment(s)");
        draggableElement.append(dragText);
        $.vakata.dnd.start(event, {
            jstree: true,
            obj: $("<a>", { id: "dnd_anchor", class: "jstree-anchor", href: "#" }),
            nodes: selectedRecords,
        }, draggableElement);
    }
};

CloudManagerKanbanRecord.template = "cloud_base.CloudManagerKanbanRecord";
