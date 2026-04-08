/** @odoo-module **/

import { KanbanRecord } from "@web/views/kanban/kanban_record";
import { x2ManyCommands } from "@web/core/orm_service";


export class AttachmentsSearchKanbanRecord extends KanbanRecord {
    /*
    * The method to add attachment to selection if needed
    */
    async onGlobalClick(ev) {
        if (ev.target.closest("a.fa-plus-circle")) {
            // we have to use x2ManyCommands.set instead of link since selected kanban then is shown incorrect
            const currentSelection = this.props.record.model.root.data.selected_attachment_ids.currentIds || [];
            currentSelection.push(this.props.record.resId);
            await this.props.record.model.root.update({
                selected_attachment_ids: [x2ManyCommands.set(currentSelection)]
            });
        }
        else if (ev.target.closest("a.fa-external-link")) {
            window.open(this.props.record.data.url, "_blank");
        }
        else {
            super.onGlobalClick(ev)
        };
    }
    /*
    * Re-write to fix the bug of double click needed to execute delete
    */
    triggerAction(params) {
        super.triggerAction(params);
        const { type } = params;
        if (type == "delete") {
            return this.props.deleteRecord(this.props.record);
        }
    }
};
