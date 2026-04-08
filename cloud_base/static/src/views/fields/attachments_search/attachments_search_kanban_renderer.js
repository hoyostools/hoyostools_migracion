/** @odoo-module **/

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { AttachmentsSearchKanbanRecord } from "./attachments_search_kanban_record";

export class AttachmentsSearchKanbanRenderer extends KanbanRenderer {};

AttachmentsSearchKanbanRenderer.components = Object.assign({}, KanbanRenderer.components, {
    KanbanRecord: AttachmentsSearchKanbanRecord,
});
