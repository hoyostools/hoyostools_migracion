/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";


export class NoArchiveListController extends ListController {
    /*
    * Re-write to always make not archivable
    */
    setup() {
        super.setup(...arguments);
        this.archiveEnabled = false;
    }
}
