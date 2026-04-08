/** @odoo-module **/

import { Chatter } from "@mail/core/web/chatter";
import { patch } from "@web/core/utils/patch";
import { CloudJsTreeContainer } from "@cloud_base/components/cloud_jstree_container/cloud_jstree_container";
import { onWillUpdateProps, onWillStart, useState } from "@odoo/owl";


patch(Chatter.prototype, {
    /*
    * Re-write to check folder existance on chatter update
    */
    setup() {
        super.setup(...arguments);
        Object.assign({ folderExist: false, cloudsFolderId: false });
        this.cloudsFolderId = false;
        onWillStart(async () => {
            await this.onCheckFolder(this.props);
        });
        onWillUpdateProps(async (nextProps) => {
            await this.onCheckFolder(nextProps);
        });
    },
    /*
    * The method to check whether the current folder exists
    */
    async onCheckFolder(nextProps) {
        const folderExist = await this.rpc(
            "/cloud_base/folder",
            { thread_id: nextProps.threadId, thread_model: nextProps.threadModel },
        );
        Object.assign(this.state, { folderExist: folderExist, cloudsFolderId: false });
    },
    /*
    * Re-write to show the attachment box disregarding whether it has or not attachments
    */
    onClickAddAttachments() {
        if (this.attachments.length === 0) {
            this.state.isAttachmentBoxOpened = !this.state.isAttachmentBoxOpened;
            if (this.state.isAttachmentBoxOpened) {
                this.rootRef.el.scrollTop = 0;
                this.state.thread.scrollTop = "bottom";
            };
        };
        super.onClickAddAttachments(...arguments)
    },
    /*
    * The method to trigger the wizard to add the attachments of the type URL
    */
    onClickAddUrl(ev) {
        this.action.doAction(
            "cloud_base.add_url_attachment_action",
            {
                additionalContext: {
                    default_folder_id: this.state.cloudsFolderId,
                    default_res_id: this.props.threadId,
                    default_res_model: this.props.threadModel,
                },
                onClose: () => {
                    var domain = [];
                    if (this.state.cloudsFolderId) {
                        domain = [["clouds_folder_id", "=", this.state.cloudsFolderId]]
                    };
                    this.onRefreshAttachmentBoxWithFolder("folders", domain, this.state.cloudsFolderId);
                },
            },
        )
    },
    /*
    * The method to prepare jstreecontainer props
    */
    getJsTreeProps(key) {
        return {
            jstreeId: key,
            onUpdateSearch: this.onRefreshAttachmentBoxWithFolder.bind(this),
            kanbanView: false,
            parentModel: this,
            resModel: this.props.threadModel,
            resId: this.props.threadId,
        }
    },
    /*
    * The method to prepare the domain by the JScontainer and notify searchmodel
    */
    async onRefreshAttachmentBoxWithFolder(jstreeId, domain, cloudsFolderId=false) {
        this.state.cloudsFolderId = cloudsFolderId || this.cloudsFolderId;
        if (this.state.thread) {
            this.threadService.refreshFolderAttachments(this.state.thread, domain, this.state.cloudsFolderId);
        }
    },
});

Chatter.components = {
    ...Chatter.components,
    CloudJsTreeContainer,
};
