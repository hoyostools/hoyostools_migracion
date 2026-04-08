/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { many2ManyTagsField, Many2ManyTagsField } from "@web/views/fields/many2many_tags/many2many_tags_field";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";


export class Many2XAutocompleteAttachments extends Many2XAutocomplete {
    static props = {
        ...Many2XAutocomplete.props,
        cloudsModel: { type: [String, Boolean], optional: true },
        cloudsResIds: { type: [String, Array, Boolean], optional: true },
    }
    /*
    * Re-write to introduce our services
    */
    setup() {
        super.setup(...arguments);
        this.dialogService = useService("dialog");
    }
    /*
    * Re-write to apply our search wizard
    */
    async onSearchMore(request) {
        const context = {
            clouds_model: this.props.cloudsModel,
            clouds_res_ids: this.props.cloudsResIds,
        };
        this.dialogService.add(FormViewDialog, {
            resModel: "compose.choose.attachments",
            title: _t("Add Attachments"),
            context,
            onRecordSaved: async (formRecord, params) => {
                const selectedRecords = formRecord.data.selected_attachment_ids.records;
                if (selectedRecords.length > 0) {
                    const recordList = formRecord.data.selected_attachment_ids.currentIds.map(x => {
                        return({ id: x});
                    });
                    this.props.update(recordList)
                }
            },
        });
    }
};

export class AttachmentsMany2many extends Many2ManyTagsField {
    static template = "cloud_base.Many2XAutocompleteAttachments"
    static components = {
        ...Many2ManyTagsField.components,
        Many2XAutocomplete: Many2XAutocompleteAttachments,
    }
    /*
    * The method to define the current model
    */
    getCloudModel() {
        if (!this.props.record.data || !this.props.record.data.model) {
            return false
        };
        return this.props.record.data.model
    }
    /*
    * The method to define the current res_ids of the mail.compose
    */
    getCloudResIds() {
        if (!this.props.record.data || !this.props.record.data.res_ids) {
            return false
        };
        return this.props.record.data.res_ids
    }
    /*
    * Re-write to pass onclick behavior
    */
    getTagProps(record) {
        const props = super.getTagProps(record);
        props.onClick = (ev) => this.onDownloadAttachment(ev, record);
        return props;
    }
    /*
    * The method to download a linked attachment
    */
    onDownloadAttachment(ev, record) {
        if (record.data.id) {
            window.open("/web/content/ir.attachment/" + record.data.id + "/datas?download=true", "_blank");
        };
    }
};

export const attachmentsSearch = {
    ...many2ManyTagsField,
    component: AttachmentsMany2many,
    supportedTypes: ["many2many"],
    relatedFields: ({ options }) => {
        const relatedFields = many2ManyTagsField.relatedFields({ options });
        relatedFields.push({ name: "id", type: "integer", readonly: true });
        return relatedFields
    },
};

registry.category("fields").add("attachments_many2many", attachmentsSearch);
