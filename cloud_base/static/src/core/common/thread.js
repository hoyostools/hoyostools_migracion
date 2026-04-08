/* @odoo-module */

import { Thread } from "@mail/core/common/thread_model";
import { patch } from "@web/core/utils/patch";


patch(Thread.prototype, {
    /*
    * Re-write to filter marked for delete attachments
    * Actually this is excess since for_delete attachments are also deactivated. However, we leave that for sudden core
    * changes
    */
    update(data) {
        if (data.attachments) {
            data.attachments = data.attachments.filter(atta => !atta.forDelete);
        };
        super.update(...arguments);
    },
});