/** @odoo-module **/

import { PartnerListScreen } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";

patch(PartnerListScreen.prototype, {
    async saveChanges(event) {
        return PartnerListScreen.prototype.saveChanges.apply(this, arguments);
    }
});


//class CustomPartnerList extends PartnerListScreen {
//    constructor() {
//        super(...arguments);
//    }
//
//    async saveChanges(event) {
//        return super.saveChanges(...arguments);
//    }
//}
//
//Registries.Component.extend(PartnerListScreen, CustomPartnerList);
//
//export default CustomPartnerList;

