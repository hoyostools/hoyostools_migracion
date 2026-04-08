/** @odoo-module **/

import { ModelFieldSelector } from "@web/core/model_field_selector/model_field_selector";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useBus } from "@web/core/utils/hooks";
import { useRecordObserver } from "@web/model/relational_model/utils";
const { Component, useState } = owl;


export class RuleParent extends Component {
    static template =  "cloud_base.RuleParent";
    static components = { ModelFieldSelector };
    static props = { ...standardFieldProps };
    /*
    * Re-write to add services
    */
    setup() {
        this.state = useState({});
        useRecordObserver(async (record) => {
            this.state.initialValue = record.data[this.props.name] || "";
            this.state.currentValue = this.state.initialValue;
            this.updateDirty(false);
        });
        const { model } = this.props.record;
        useBus(model.bus, "WILL_SAVE_URGENTLY", () => this.commitChanges());
        useBus(model.bus, "NEED_LOCAL_CHANGES", ({ detail }) => detail.proms.push(this.commitChanges()));
    }
    /*
    * The method to handle a temporary change (no save yet)
    */
    async handleChange(currentValue) {
        if (this.state.initialValue !== currentValue) {
            this.updateDirty(true);
        }
        else {
            this.updateDirty(false)
        };
        this.state.currentValue = currentValue;
        await this.props.record.update({ [this.props.name]: currentValue });
    }
    /*
    * The method to commit changes (so save to the record)
    */
    async commitChanges() {
        if (!this.props.readonly && this.isDirty) {
            if (this.state.initialValue !== this.state.currentValue) {
                await this.props.record.update({ [this.props.name]: this.state.currentValue });
            };
        };
        this.updateDirty(false)
    }
    /*
    * The method to trigger dirty update
    */
    updateDirty(isDirty) {
        this.isDirty = isDirty;
        this.props.record.model.bus.trigger("FIELD_IS_DIRTY", this.isDirty);
    }
    /*
    * Get res_model name from the 'model' field
    */
    getResModel() {
        let resModel = "";
        if (this.props.record.fieldNames.includes("model")) {
            resModel = this.props.record.data["model"];
        }
        return resModel;
    }
    /*
    * Filter method of fields selector, the idea is to show only m2o fields
    */
    getFieldsFilter(field) {
        return field.type == "many2one";
    }
    /*
    * The method to remove the chosen field
    */
    clear() {
        this.handleChange(false);
    }
};

export const ruleParent = {
    component: RuleParent,
    supportedTypes: ["char"],
};

registry.category("fields").add("parentRuleMany2one", ruleParent);
