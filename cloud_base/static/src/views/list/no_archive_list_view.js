/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { NoArchiveListController } from "./no_archive_list_controller";


export const NoArchiveListView = {
	...listView,
    Controller: NoArchiveListController,
};

registry.category("views").add("no_archive_tree", NoArchiveListView);
