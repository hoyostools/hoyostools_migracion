/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(OrderWidget.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },

    get orderlines(){
        let order = this.pos.get_order();
        var orderlines = order.get_orderlines();
        return orderlines;
    },

    get product_total(){
        let order = this.pos.get_order();
        var orderlines = order.get_orderlines();
        return orderlines.length;
    },

});