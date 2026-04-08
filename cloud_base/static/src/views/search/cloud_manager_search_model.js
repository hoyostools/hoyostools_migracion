/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { Domain } from "@web/core/domain";
import { SearchModel } from "@web/search/search_model";


export class CloudManagerSearchModel extends SearchModel {
    /*
    * Overwrite to introduce jsTreeDomain
    */
    setup(services) {
        this.jsTreeDomain = [];
        super.setup(...arguments);
    }
    /*
    * Overwrite to add our jsTree
    * Regretfully, none of child method can be triggered, so we have to redefine the whole return
    */
    _getDomain(params = {}) {
        var domain =  super._getDomain(...arguments);
        try {
            domain = Domain.and([domain, this.jsTreeDomain]);
            return params.raw
                ? domain
                : domain.toList(Object.assign({}, this.globalContext, this.userService.context));
        } catch (error) {
            throw new Error(
                _t("Failed to evaluate the domain: %(domain)s.\n%(error)s", {
                    domain: domain.toString(),
                    error: error.message,
                })
            );
        };
    }
    /*
    * The method to save received jsTree domain
    */
    toggleJSTreeDomain(domain) {
        this.jsTreeDomain = domain;
        this._notify();
    }
}
