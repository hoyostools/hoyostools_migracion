/** @odoo-module **/

import { AttachmentList } from "@mail/core/common/attachment_list";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";


patch(AttachmentList.prototype, {
    /*
    * Re-write to add orm
    */
    setup() {
        this.orm = useService("orm");
        super.setup(...arguments);
    },
    /*
    * Re-write to make any synced attachments to be not image even if it is
    */
    get nonImagesAttachments() {
        return this.props.attachments.filter((attachment) => !attachment.isImage || attachment.cloudURL);
    },
    /*
    * Re-write to make any synced attachments to be not image even if it is
    */
    get imagesAttachments() {
        return this.props.attachments.filter((attachment) => attachment.isImage && !attachment.cloudURL);
    },
    /*
    * The method is introduced instead of this.fileViewer.open(attachment, props.attachments) in template
    * The goal is to open cloud URLs when that is possible
    */
    onPreviewOpen(file, files) {
        if (!file.cloudSynced || file.isViewable) {
            return this.fileViewer.open(file, files);
        }
        else {
            this.onClickOpenCloudLink(file);
        }
    },
    /*
    * The method to open the cloud URL if any
    */
    async onClickOpenCloudLink(attachment) {
        const cloudURL = await this.orm.call("ir.attachment", "action_retrieve_url", [[attachment.id]]);
        const cloudLink = document.createElement("a");
        cloudLink.setAttribute("href", cloudURL);
        cloudLink.setAttribute("target", "_blank");
        cloudLink.click();
    },
});
