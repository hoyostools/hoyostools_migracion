/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, useState } = owl;
const componentModel = "clouds.folder";


export class CloudManager extends Component {
    static template = "cloud_base.CloudManager";
    static props = {
        currentSelection: { type: Array },
        selection: { type: Array },
        kanbanModel: { type: Object },
        canCreate: { type: Boolean },
        reloadNavigation: { type: Function },
    };
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.orm = useService("orm");
        this.state = useState({ massActions: null });
        this.dialogService = useService("dialog");
        this.actionService = useService("action");
        this.rpc = useService("rpc");
        onWillStart(async () => {
            await this._loadMassActions(this.props);
        });
    }
    /*
    * Getter for records from selection
    */
    get records() {
        var result = null;
        if (this.props.selection && this.props.selection.length != 0) {
            result = this.props.selection;
        };
        return result
    }
    /*
    * The method to get configured mass actions
    */
    async _loadMassActions(props) {
        var massActions = await this.orm.call(componentModel, "action_return_mass_actions", []);
        if (massActions.length === 0) {
            massActions = null;
        }
        Object.assign(this.state, { massActions: massActions });
    }
    /*
    * The method to execute clicked mass action
    */
    async _onProceedMassAction(massActionID) {
        const recordIds = this.props.selection.map((rec) => rec.id);
        const actionResult = await this.orm.call(
            componentModel, "action_proceed_mass_action", [recordIds, massActionID],
        );
        if (actionResult.type) {
            this.actionService.doAction(actionResult,  { onClose: async () => {
                await this._updateRootSelection(recordIds);
                this._refreshAfterUpdate();
                if (actionResult.context && actionResult.context.need_navigation_reload) {
                    this.props.reloadNavigation();
                };
            }})
        } else {
            await this._updateRootSelection(recordIds);
            await this._refreshAfterUpdate();
            if (actionResult.delete) {
                this._onClearSelection()
            };
        };
    }
    /*
    * The method to update selected records after update (e.g. when record was deleted)
    */
    async _updateRootSelection(recordIds) {
        const context = { active_test: false };
        this.props.kanbanModel.selectedRecords = await this.orm.searchRead(
            "ir.attachment", [["id", "in", recordIds]], ["name"], { context }
        );
    }
    /*
    * The method to load updated records after mass update
    */
    async _refreshAfterUpdate() {
        await this.props.kanbanModel.root.load();
        this.props.kanbanModel.notify();
    }
    /*
    * The method to remove a record from selection
    */
    _onRemoveFromSelection(recordId) {
        var record = this.props.currentSelection.find(rec => rec.resId === recordId);
        if (record) {
            record.toggleSelection(false);
        } else {
            record = this.props.selection.find(rec => rec.id === recordId);
            this.props.kanbanModel._updateModelSelection(record, false);
            this._refreshAfterUpdate();
        };
    }
    /*
    * Remove all previously chosen records from selection
    */
    _onClearSelection() {
        const kanbanModel = this.props.kanbanModel;
        const needReload = this.props.currentSelection.length === 0;
        this.props.currentSelection.forEach(function (record) {
            record.toggleSelection(false);
        });
        this.props.selection.forEach(function (record) {
            kanbanModel._updateModelSelection(record, false);
        });
        if (needReload) {
            this._refreshAfterUpdate();
        };
    }
};
