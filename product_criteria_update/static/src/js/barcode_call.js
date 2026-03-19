/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { scanBarcode, BarcodeDialog } from "@web/webclient/barcode/barcode_scanner";

export class CallBarcode extends Component {
    static props = ["*"];
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");
    }

    async call_cam_barcode(){
        let data;
            try {
                data = await scanBarcode(this.env);
            } catch (error) {
                if (error.error && error.error.message) {
                    this.popup.add(ErrorPopup, {
                        title: _t("No escaneable"),
                        body: error.error.message,
                    });
                    return;
                }
                throw error;
            }
            if (data) {
                const product = await this.orm.search('product.product', [['barcode', '=', data]]);
                if (product.length === 0) {
                    this.notification.add("Producto no encontrado", {
                        type: "warning",
                    });
                } else {
                    const productData = await this.orm.read('product.product', product, ['display_name']);
                    this.props.record.data.product_id = [product[0], productData[0].display_name];
                    this.props.record._changes.product_id = [product[0], productData[0].display_name];
                }
            } else {
                this.env.services.notification.notify({
                    type: "warning",
                    message: "Por favor, escanee nuevamente!",
                });
            }
    }

    async call_cam_barcode_location(){
        let data;
            try {
                data = await scanBarcode(this.env);
            } catch (error) {
                if (error.error && error.error.message) {
                    // Here, we know the structure of the error raised by BarcodeScanner.
                    this.popup.add(ErrorPopup, {
                        title: _t("No escaneable"),
                        body: error.error.message,
                    });
                    return;
                }
                // Just raise the other errors.
                throw error;
            }
            if (data) {
                const location = await this.orm.search('stock.location', [['barcode', '=', data]]);
                const locationData = await this.orm.read('stock.location', product, ['display_name']);
                this.props.record.data.location_id = [location[0], locationData[0].display_name];
                this.props.record._changes.location_id = [location[0], locationData[0].display_name];
            } else {
                this.env.services.notification.notify({
                    type: "warning",
                    message: "Por favor, escanee nuevamente!",
                });
            }
    }

}

CallBarcode.template = "call_barcode";

export const CallBarcodeD = {
    component: CallBarcode,
    supportedTypes: ["char"]
};

registry.category("fields").add("widget_barcode", CallBarcodeD);

export class CallBarcodeLocation extends Component {
    static props = ["*"];
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");
    }

    async call_cam_barcode_location(){
        let data;
            try {
                data = await scanBarcode(this.env);
            } catch (error) {
                if (error.error && error.error.message) {
                    this.popup.add(ErrorPopup, {
                        title: _t("No escaneable"),
                        body: error.error.message,
                    });
                    return;
                }
                throw error;
            }
            if (data) {
                const location = await this.orm.search('stock.location', [['barcode', '=', data]]);
                if (location.length === 0) {
                    this.notification.add("Ubicación no encontrada", {
                        type: "warning",
                    });
                } else {
                    const locationData = await this.orm.read('stock.location', location, ['display_name']);
                    this.props.record.data.location_id = [location[0], locationData[0].display_name];
                    this.props.record._changes.location_id = [location[0], locationData[0].display_name];
                }
            } else {
                this.env.services.notification.notify({
                    type: "warning",
                    message: "Por favor, escanee nuevamente!",
                });
            }
    }

}

CallBarcodeLocation.template = "call_barcode_location";

export const CallBarcodeL = {
    component: CallBarcodeLocation,
    supportedTypes: ["char"]  // Puedes cambiar esto según el tipo de campo que estés usando
};

registry.category("fields").add("widget_barcode_location", CallBarcodeL);