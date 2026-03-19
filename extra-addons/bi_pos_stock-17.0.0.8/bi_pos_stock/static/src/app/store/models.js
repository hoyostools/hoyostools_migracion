/** @odoo-module */
import { Order } from "@point_of_sale/app/store/models";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(loadedData);
        this.custom_stock_locations = loadedData['stock.location'] || [];
    },

    async addProductToCurrentOrder(product, options = {}) {
        let self = this;
        let pos_config = self.config;
        let allow_order = pos_config.pos_allow_order;
        let deny_order= pos_config.pos_deny_order || 0;
        let call_super = true;

        if(pos_config.pos_display_stock && product.type == 'product'){
            if (allow_order == false){
                if (pos_config.pos_stock_type == 'onhand'){
                    if ( product.bi_on_hand <= 0 ){
                        call_super = false;
                        self.popup.add(ErrorPopup, {
                            title: _t('Deny Order'),
                            body: _t("Deny Order" + "(" + product.display_name + ")" + " is Out of Stock."),
                        });
                    }
                }
                if (pos_config.pos_stock_type == 'available'){
                    if ( product.bi_available <= 0 ){
                        call_super = false;
                        self.popup.add(ErrorPopup, {
                            title: _t('Deny Order'),
                            body: _t("Deny Order" + "(" + product.display_name + ")" + " is Out of Stock."),
                        });
                    }
                }
            }else{
                if (pos_config.pos_stock_type == 'onhand'){
                    if ( product.bi_on_hand <= deny_order ){
                        call_super = false;
                        self.popup.add(ErrorPopup, {
                            title: _t('Deny Order'),
                            body: _t("Deny Order" + "(" + product.display_name + ")" + " is Out of Stock."),
                        });
                    }
                }
                if (pos_config.pos_stock_type == 'available'){
                    if ( product.bi_available <= deny_order ){
                        call_super = false;
                        self.popup.add(ErrorPopup, {
                            title: _t('Deny Order'),
                            body: _t("Deny Order" + "(" + product.display_name + ")" + " is Out of Stock."),
                        });
                    }
                }
            }
        }
        if(call_super){
            super.addProductToCurrentOrder(product, options = {});
        }
    }       
});

patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
    },

    product_total(){
        let order = this.pos.get_order();
        var orderlines = order.get_orderlines();
        return orderlines.length;
    },

    set_interval(interval){
        this.interval=interval;
    },

    async pay() {
        var self = this;
        let order = this.pos.get_order();
        let lines = order.get_orderlines();
        let pos_config = self.pos.config; 
        let allow_order = pos_config.pos_allow_order;
        let deny_order= pos_config.pos_deny_order || 0;
        let call_super = true;

        if(pos_config.pos_display_stock){
            let prod_used_qty = {};
            $.each(lines, function( i, line ){
                let prd = line.product;
                if (prd.type == 'product'){
                    if(pos_config.pos_stock_type == 'onhand'){
                        if(prd.id in prod_used_qty){
                            let old_qty = prod_used_qty[prd.id][1];
                            prod_used_qty[prd.id] = [prd.bi_on_hand,line.quantity+old_qty]
                        }else{
                            prod_used_qty[prd.id] = [prd.bi_on_hand,line.quantity]
                        }
                    }
                    if(pos_config.pos_stock_type == 'available'){
                        if(prd.id in prod_used_qty){
                            let old_qty = prod_used_qty[prd.id][1];
                            prod_used_qty[prd.id] = [prd.bi_available,line.quantity+old_qty]
                        }else{
                            prod_used_qty[prd.id] = [prd.bi_available,line.quantity]
                        }
                    }

                    
                }
            });

            $.each(prod_used_qty,await function( i, pq ){
                let product = self.pos.db.get_product_by_id(i);
                if (allow_order == false && pq[0] < pq[1]){
                    call_super = false;
                    self.pos.popup.add(ErrorPopup, {
                        title: _t('Deny Order'),
                        body: _t("Deny Order" + "(" + product.display_name + ")" + " is Out of Stock."),
                    });
                }
                let check = pq[0] - pq[1];
                if (allow_order == true && check < deny_order){
                    call_super = false;
                    self.pos.popup.add(ErrorPopup, {
                        title: _t('Deny Order'),
                        body: _t("Deny Order" + "(" + product.display_name + ")" + " is Out of Stock."),
                    });
                }
            });
        }

        if(call_super){
            super.pay();
        }
    },
});