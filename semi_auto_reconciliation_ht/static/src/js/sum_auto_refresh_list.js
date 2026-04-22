/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";

export class RefreshSumListController extends ListController {

    async onRecordSaved(record) {

        const res = await super.onRecordSaved(...arguments);

        if ("amount_to_apply" in record.data) {

            setTimeout(async () => {

                if (this.model.root) {

                    await this.model.root.load();
                    this.render(true);

                }

            }, 0);

        }

        return res;
    }

}

export const RefreshSumListView = {
    ...listView,
    Controller: RefreshSumListController,
};

registry.category("views").add("refresh_sum_list", RefreshSumListView);
