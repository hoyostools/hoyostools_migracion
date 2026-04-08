/** @odoo-module **/

import { registry } from "@web/core/registry";
import { x2ManyField, X2ManyField } from "@web/views/fields/x2many/x2many_field";
import { AttachmentsSearchKanbanRenderer } from "./attachments_search_kanban_renderer";


export class AttachmentsSearch extends X2ManyField {
    static components = { ...X2ManyField.components, KanbanRenderer: AttachmentsSearchKanbanRenderer };
};

export const attachmentsSearch = {
    ...x2ManyField,
    component: AttachmentsSearch,
    supportedTypes: ["many2many"],
};

registry.category("fields").add("attachments_search", attachmentsSearch);
