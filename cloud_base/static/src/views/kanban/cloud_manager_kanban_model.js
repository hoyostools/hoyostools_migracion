/** @odoo-module **/

import { CloudManagerKanbanDynamicRecordList } from "./cloud_manager_kanban_dynamic_list";
import { RelationalModel } from "@web/model/relational_model/relational_model";
import { Record } from "@web/model/relational_model/record";


export class CloudManagerKanbanRecord extends Record {
    /**
    * The method to manage kanban records clicks: to add an item to selection
    */
    onRecordClick(ev, options = {}) {
        this.toggleSelection(!this.selected);
    }
    /*
    * Overwrite to save selection for model, not only in a record. The idea is to not update selection after each reload
    */
    toggleSelection(selected) {
        super.toggleSelection(selected);
        this.model._updateModelSelection({"id": this.resId, "name": this.data.name}, selected);
    }
};

export class CloudManagerKanbanModel extends RelationalModel {
    static Record = CloudManagerKanbanRecord;
    static DynamicRecordList = CloudManagerKanbanDynamicRecordList;
    /*
    * Re-write to introduce selected records, so our list will be restored from previous selection (if any)
    */
    setup(params, { action, company, dialog, notification, rpc, user }) {
        if (params.state) {
            this.selectedRecords = params.state.selectedRecords || [];
        }
        else {
            this.selectedRecords = [];
        }
        super.setup(...arguments);
    }
    /*
    * The method to add/remove record from SelectedRecords
    */
    _updateModelSelection(record, selected) {
        if (selected) {
            this.selectedRecords.push(record)
        }
        else {
            this.selectedRecords = this.selectedRecords.filter(rec => rec.id != record.id)
        };
    }
    /*
    * Overwrite to save selected records to state
    */
    exportState() {
        const state = {
            ...super.exportState(),
            selectedRecords: this.selectedRecords,
        };
        return state
    }
};
