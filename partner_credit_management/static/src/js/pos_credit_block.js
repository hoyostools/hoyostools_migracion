/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";


patch(Order.prototype, {

    async set_partner(partner) {

        if (partner && partner.credit_blocked) {

            this.pos.popup.add(ErrorPopup, {
                title: "Cliente bloqueado",
                body: "Este cliente se encuentra bloqueado. Por favor contacte al área de cartera.",
            });

            return;
        }

        return await super.set_partner(...arguments);
    },
});