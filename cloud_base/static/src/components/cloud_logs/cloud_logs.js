/** @odoo-module **/

import { _lt } from "@web/core/l10n/translation";
import { formatDateTime, parseDateTime } from "@web/core/l10n/dates";
import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { useDateTimePicker } from "@web/core/datetime/datetime_hook";
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted, onPatched, onWillDestroy, onWillStart, useState } = owl;

const componentModel = "clouds.log";
const SERVER_DATE_FORMAT = "yyyy-MM-dd HH:mm:ss"


export class CloudLogs extends Component {
    static template = "cloud_base.CloudLogs";
    static props = { ... standardActionServiceProps };
    /*
    * Re-write to import required services and update props on the component start
    */
    setup() {
        this.searchString = "";
        this.refreshInterval = false;
        this.needPatch = false;
        this.state = useState({
            loadMore: false,
            firstLog: false,
            lastLog: false,
            cloudClients: [],
            selectedClients: [],
            activeTasks: 0,
            failedTasks: 0,
            logLevels: ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
            selectedLogLevels: [],
            searchString: false,
            dateStart: null,
            dateEnd: null,
        });
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.uiService = useService("ui");

        const getPickerProps = () => {
            const value = [this.dateStartLocal, this.dateEndLocal];
            const pickerProps = { value, type: "datetime", range: true };
            return pickerProps;
        };
        const dateTimePicker = useDateTimePicker({
            target: "root",
            get pickerProps() { return getPickerProps() },
            onApply: () => {
                this._onDatesChange(this.state.dateTimePickerState.value);
            },
        });
        Object.assign(this.state, { dateTimePickerState: dateTimePicker.state });
        onWillStart(async () => {
            await this._onLoadAllElements();
        });
        onMounted( async () => {
            this.logsWrapContainer = $(".cloud-logs-screen-wrap");
            this.logsMainContainer = $(".cloud-logs-main");
            this.logsMain = this.logsMainContainer[0];
            this.logsMoreBtn = $(".clouds-logs-more-btn-div");
            this.cloudLogsSearchInput = $("#cloud_logs_search_input")[0];
            this.logsMain.innerHTML = this.htmlLogs;
            this._scrollToTheBottom(false);
            this._setRefreshInterval();
        });
        onPatched( async() => {
            if (this.needPatch) {
                this._scrollToTheBottom(false);
                this._setRefreshInterval();
                this.needPatch = false;
            };
        });
        onWillDestroy( () => {
            this._clearRefreshInterval();
        });
    }
    /*
    * Getter for the dateStartLocal to parse the dateStart in the correct locale
    */
    get dateStartLocal() {
        return this.state.dateStart ? parseDateTime(this.state.dateStart) : false;
    }
    /*
    * Getter for the dateEndLocal to parse the dateEnd in the correct locale
    */
    get dateEndLocal() {
        return this.state.dateEnd ? parseDateTime(this.state.dateEnd) : false;
    }
    /*
    * The method to assign the logs values on load or refresh
    */
    async _onLoadSyncLogs() {
        const syncLogsDict = await this._loadSyncLogs();
        Object.assign(this.state, {
            loadMore: syncLogsDict.load_more_btn,
            firstLog: syncLogsDict.first_log,
            lastLog: syncLogsDict.last_log,
        });
        this.htmlLogs = syncLogsDict.log_html || "";
        if (this.logsMain) {
            this.logsMain.innerHTML = this.htmlLogs;
        };
    }
    /*
    * The method to refresh logs
    */
    async _onRefreshSyncLogs() {
        const newLogsDict = await this._loadSyncLogs({ "last_log": this.state.lastLog });
        if (newLogsDict.log_html) {
            Object.assign(this.state, { lastLog: newLogsDict.last_log });
            this.logsMain.innerHTML = this.logsMain.innerHTML + newLogsDict.log_html;
        }
    }
    /*
    * The method to get all available cloud clients
    * Note: client might be changed without interactions
    */
    async _onLoadCloudClients() {
        const cloudClients = await this.orm.call(componentModel, "action_get_cloud_clients", [this.state.selectedClients]);
        if (this.state.cloudClients != cloudClients) {
            Object.assign(this.state, { cloudClients: cloudClients });
        };
    }
    /*
    * The method to get the topical queue
    * Note: tasks might be changed without interactions
    */
    async _onLoadQueue() {
        const logsQueue = await this.orm.call(componentModel, "action_get_cloud_queue", [this.state.selectedClients]);
        if (this.state.activeTasks != logsQueue.active_tasks || this.state.failedTasks != logsQueue.failed_tasks) {
            Object.assign(this.state, {
                activeTasks: logsQueue.active_tasks,
                failedTasks: logsQueue.failed_tasks,
            });
        }
    }
    /*
    * Trigger simple refreshing (without recalculation)
    */
    async _onLoadAllElements() {
        const proms = [
            this._onLoadQueue(),
            this._onLoadCloudClients(),
            this._onLoadSyncLogs(),
        ]
        return Promise.all(proms);
    }
    /*
    * Trigger simple refreshing (without recalculation)
    */
    async _onRefreshAllElements() {
        const proms = [
            this._onLoadQueue(),
            this._onLoadCloudClients(),
            this._onRefreshSyncLogs(),
        ]
        return Promise.all(proms);
    }
    /*
    * The method to show previous logs based on the "more" button click
    */
    async onLoadMoreLogs(event) {
        event.preventDefault();
        event.stopPropagation();
        const newLogsDict = await this._loadSyncLogs({ "first_log": this.state.firstLog });
        if (newLogsDict.log_html) {
            Object.assign(this.state, {
                firstLog: newLogsDict.first_log,
                loadMore: newLogsDict.load_more_btn,
            });
            this.logsMain.innerHTML = newLogsDict.log_html + this.logsMain.innerHTML;
        };
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
    async _onSearchExecute() {
        this._clearRefreshInterval();
        this.state.searchString = this.searchString;
        await this._onLoadAllElements();
        this.needPatch = true;
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
        this.cloudLogsSearchInput.value = "";
        this.searchString = "";
        this._onSearchExecute();
    }
    /*
    * The method to turn on/off a sprcific cloud client
    */
    async _onToggleCloudClient(event, cloudClient) {
        this._clearRefreshInterval();
        if (event.currentTarget.checked) {
            if (!this.state.selectedClients.some((element) => element === cloudClient)) {
                this.state.selectedClients.push(cloudClient)
            }
        }
        else {
            this.state.selectedClients = this.state.selectedClients.filter(function(value, index, arr) {
                return value != cloudClient;
            });
        };
        await this._onLoadAllElements();
        this.needPatch = true;
    }
    /*
    * The method to turn on/off a sercific log level
    */
    async _onToggleLogLevel(event, logLevel) {
        this._clearRefreshInterval();
        if (event.currentTarget.checked) {
            if (!this.state.selectedLogLevels.some((element) => element === logLevel)) {
                this.state.selectedLogLevels.push(logLevel)
            }
        }
        else {
            this.state.selectedLogLevels = this.state.selectedLogLevels.filter(function(value, index, arr) {
                return value != logLevel;
            });
        };
        await this._onLoadAllElements();
        this.needPatch = true;
    }
    /*
    * The method to process the period change
    */
    async _onDatesChange(date) {
        Object.assign(this.state, {
            dateStart: date[0] ? formatDateTime(date[0], { format: SERVER_DATE_FORMAT }) : false,
            dateEnd: date[1] ? formatDateTime(date[1], { format: SERVER_DATE_FORMAT }) : false,
        });
        await this._onLoadAllElements();
        this.needPatch = true;
    }

    /*
    * The method to open cloud client
    */
    async _onOpenCloudClient(cloudClient) {
        if (Number.isInteger(cloudClient)) {
            const action = await this.orm.call("clouds.client", "action_get_formview_action", [cloudClient]);
            this.actionService.doAction(action);
        };
    }
    /*
    * The method to open the queue
    */
    async _onOpenQueue(onlyFailed) {
        const action = await this.orm.call("clouds.log", "action_open_tasks", [this.state.selectedClients, onlyFailed]);
        this.actionService.doAction(action);
    }
    /*
    * The method to save filtered logs as txt
    */
    async _onExportLogs() {
        this.uiService.block();
        await download({
            url: "/cloud_base/export_logs",
            data: {
                search_name: this.state.searchString || "",
                selected_clients: JSON.stringify(this.state.selectedClients),
                log_levels: JSON.stringify(this.state.selectedLogLevels),
                period: JSON.stringify([this.state.dateStart, this.state.dateEnd]),
            },
        });
        this.uiService.unblock();
    }
    /*
    * The method to get sync logs satisfying the last criteria
    */
    async _loadSyncLogs(logArgsDict) {
        const localArguments = logArgsDict || {};
        const syncLogsDict = await this.orm.call(
            componentModel,
            "action_prepare_logs_html",
            [
                localArguments,
                this.state.searchString,
                this.state.selectedClients,
                this.state.selectedLogLevels,
                [this.state.dateStart, this.state.dateEnd],
            ],
        )
        return syncLogsDict
    }
    /*
     * The method to refresh logs, queue, and cloud clients
    */
    _setRefreshInterval() {
        this._clearRefreshInterval();
        this.refreshInterval = setInterval(async() => {
            const baseHeight = this.logsMainContainer.height() + 20 + this.logsMoreBtn.height();
            await this._onRefreshAllElements();
            this._scrollToTheBottom(baseHeight);
        }, 6000); // once in 6 seconds
    }
    /*
     * The method to cancel the auto update
    */
    _clearRefreshInterval() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval)
        };
    }
    /*
    * Scroll to the logs bottom
    */
    _scrollToTheBottom(baseHeight) {
        const scrollHeight = this.logsMainContainer.height() + 20 + this.logsMoreBtn.height();
        if (baseHeight) {
            if (baseHeight - (this.logsWrapContainer.scrollTop() + this.logsWrapContainer.height()) > 200) {
                return
            }
        };
        this.logsWrapContainer.animate({scrollTop: scrollHeight}, 100);
        this.previousHeight = scrollHeight;
    }
}

registry.category("actions").add("cloud.base.log", CloudLogs);
