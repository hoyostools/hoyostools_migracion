/* @odoo-module */

import { ThreadService } from "@mail/core/common/thread_service";
import { patch } from "@web/core/utils/patch";


patch(ThreadService.prototype, {
    /*
    * Re-write to refetch attachment folders on their change (mainly for message attachments)
    */
    async fetchData(
        thread,
        requestList = ["activities", "followers", "attachments", "messages", "suggestedRecipients"]
    ) {
        const result = await super.fetchData(...arguments)
        if (thread.folderDomain && thread.cloudsFolderId) {
            await this.fetchFolderAttachments(thread);
        };
        return result
    },
    /*
    * The method to get attachments linked to the currently selected folder
    */
    async fetchFolderAttachments(thread) {
        const attachmentsData = await this.rpc(
            "/cloud_base/attachments/data",
            {
                thread_id: thread.id,
                thread_model: thread.model,
                checked_folder: thread.cloudsFolderId || false,
                folder_domain: thread.folderDomain || [],
            },
        );
        thread.update({ attachments: attachmentsData });
    },
    /*
    * The method to refresh attachment box when checked folder is changed
    */
    async refreshFolderAttachments(thread, folderDomain, cloudsFolderId) {
        Object.assign(thread, { folderDomain: folderDomain, cloudsFolderId: cloudsFolderId});
        this.fetchFolderAttachments(thread)
    },
});
