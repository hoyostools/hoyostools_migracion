/* @odoo-module */

import { AttachmentUploadService } from "@mail/core/common/attachment_upload_service";
import { patch } from "@web/core/utils/patch";


patch(AttachmentUploadService.prototype, {
    /*
    * Re-write to pass thread folder for the upload controller
    */
    _makeFormData(formData, file, hooker, tmpId, options) {
        if (hooker.thread && hooker.thread.cloudsFolderId && !hooker.composer) {
            formData.append("clouds_folder_id", parseInt(hooker.thread.cloudsFolderId));
        };
        return super._makeFormData(...arguments);
    }
});
