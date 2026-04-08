/** @odoo-module **/

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { CloudDropZone } from "@cloud_base/components/cloud_upload_zone/cloud_upload_zone";
import { CloudManagerKanbanRecord } from "./cloud_manager_kanban_record";
import { CloudManager } from "@cloud_base/components/cloud_manager/cloud_manager";
import { CloudNavigation } from "@cloud_base/components/cloud_navigation/cloud_navigation";
import { useState } from "@odoo/owl";


export class CloudManagerKanbanRenderer extends KanbanRenderer {
    /*
    * Re-write to initialize state for dropzone
    */
    setup() {
        super.setup();
        this.state.dropzoneVisible = false;
    }
    /*
    * Prepare props for the CloudManagerManager (right navigation & mass actions component)
    */
    getCloudManagerManagerProps() {
        return {
            currentSelection: this.props.list.selection,
            selection: this.props.list.model.selectedRecords,
            kanbanModel: this.props.list.model,
            canCreate: this.props.archInfo.activeActions.create,
            reloadNavigation: this._reloadNavigation.bind(this),
        };
    }
    /*
    * The method to CloudManagerNavigation (left navigation)
    */
    getCloudManagerNavigationProps() {
        return {
            kanbanList: this.props.list,
            kanbanModel: this.props.list.model,
        }
    }
    /*
    * The method to make dropzone visible
    */
    makeDropZoneVisible(event) {
        if (event.dataTransfer.effectAllowed != "move") {
           // Otherwise we consider it as an attachment
           this.state.dropzoneVisible = true;
        };
    }
    /*
    * The method to update the navigation panel
    */
    _reloadNavigation() {
        Object.assign(this.state, { "reloaded": !this.state.reloaded })
    }
};

CloudManagerKanbanRenderer.template = "cloud_base.CloudManagersKanbanRenderer";
CloudManagerKanbanRenderer.components = Object.assign({}, KanbanRenderer.components, {
    CloudManager,
    CloudNavigation,
    CloudDropZone,
    KanbanRecord: CloudManagerKanbanRecord,
});
