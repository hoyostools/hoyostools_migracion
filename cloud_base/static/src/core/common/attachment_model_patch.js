/* @odoo-module */

import { Attachment } from "@mail/core/common/attachment_model";
import { patch } from "@web/core/utils/patch";


patch(Attachment.prototype, {
    /*
    * Re-write to make simple links not viewable
    */
    get isViewable() {
        if (!this.cloudSynced && this.cloudURL) {
            return false
        }
        return super.isViewable;
    },
    /*
    * Re-write to make cloud url correct downloadable
    */
    get isUrl() {
        return this.type === "url" && this.url && !this.cloudSynced;
    }

});
