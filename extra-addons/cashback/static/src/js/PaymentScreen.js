/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { rpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const currentOrder = this.currentOrder;
        const plines = currentOrder.get_paymentlines();
        let total_cashback = 0;
        let partner = await currentOrder.get_partner();

        // Obtener datos actualizados del partner desde el servidor

        partner = await this.orm.searchRead(
                    "res.partner",                    // Modelo
                    [['id', '=', partner.id]],        // Dominio (condición de búsqueda)
                    ['blocking_amount', 'days_unreconciled_10', 'over_permision_unreconciled_10', 'attended_event', 'active_cashback_limit'] // Campos que deseas leer
                );

        partner = partner[0]


        for (const pline of plines) {
            if (pline.payment_method.is_cashback === true) {
                total_cashback += pline.amount;
            }
        }

        const division_result = (currentOrder.get_total_with_tax() / 1000).toFixed(1);

        for (const key in currentOrder.couponPointChanges) {
            if (currentOrder.couponPointChanges[key]['points'] === division_result) {
                currentOrder.couponPointChanges[key]['points'] = (currentOrder.get_total_without_tax() / 1000).toFixed(1);
            }
        }

        if (total_cashback > 0) {
            if (partner.days_unreconciled_10 && !partner.over_permision_unreconciled_10) {
                this.popup.add(ErrorPopup, {
                    title: _t('Not Allowed'),
                    body: _t(`El cliente ${partner.name}, tiene deuda pendiente de 10 días o más, no puede usar Cashback.`),
                });
                return;
            }

            if (total_cashback > partner.blocking_amount) {
                this.popup.add(ErrorPopup, {
                    title: _t('Not Allowed'),
                    body: _t(`El valor de pago con Cashback es mayor a la cantidad de Cashback del cliente ${partner.name}, debe ser máximo $${partner.blocking_amount}.`),
                });
                return;
            }

            if (!partner.attended_event) {
                this.popup.add(ErrorPopup, {
                    title: _t('Not Allowed'),
                    body: _t('El cliente no asistió al evento, no puede usar Cashback.'),
                });
                return;
            }

            if (!partner.active_cashback_limit) {
                this.popup.add(ErrorPopup, {
                    title: _t('Not Allowed'),
                    body: _t('El cliente seleccionado no tiene activo el Cashback, no puede usar este método de Pago'),
                });
                return;
            }

            if (total_cashback > 0) {
                currentOrder.couponPointChanges = {};
            }
        }

        super.validateOrder(...arguments);
//        return PaymentScreen.prototype.validateOrder.apply(this, arguments);
    }
});



//odoo.define('hoyostools_cashback.customPaymentScreen', function(require) {
//    'use strict';
//
//    const PaymentScreen = require('point_of_sale.PaymentScreen');
//    const Registries = require('point_of_sale.Registries');
//    const ErrorPopup = require('point_of_sale.ErrorPopup');
//    const rpc = require('web.rpc');
//    const { _t } = require('web.core');
//
//    const CustomPaymentScreen = (PaymentScreen) => class extends PaymentScreen {
//        constructor() {
//            super(...arguments);
//            this.popup = this.showPopup;
//        }
//
//        async validateOrder(isForceValidate) {
//            var self = this;
//            var currentOrder = this.env.pos.get_order();
//            var plines = currentOrder.get_paymentlines();
//            var total_cashback = 0;
//            var partner = await this.env.pos.get_order().get_partner();
//
//            // Obtener datos actualizados del partner desde el servidor
//            partner = await rpc.query({
//                model: 'res.partner',
//                method: 'read',
//                args: [[partner.id], ['blocking_amount', 'days_unreconciled_10', 'over_permision_unreconciled_10', 'attended_event', 'active_cashback_limit']],
//            }).then(partners => partners[0]);
//
//            for (var i = 0; i < plines.length; i++) {
//                if (plines[i].payment_method.is_cashback === true) {
//                    total_cashback += plines[i].amount;
//                }
//            }
//
//            var division_result = (currentOrder.get_total_with_tax() / 1000).toFixed(1);
//
//            for (var key in currentOrder.couponPointChanges) {
//                if (currentOrder.couponPointChanges[key]['points'] == division_result) {
//                    currentOrder.couponPointChanges[key]['points'] = (currentOrder.get_total_without_tax() / 1000).toFixed(1);
//                }
//            }
//
//            if (total_cashback > 0) {
//                if (partner.days_unreconciled_10) {
//                    if (partner.over_permision_unreconciled_10) {
//                    } else {
//                        this.showPopup('ErrorPopup', {
//                            'title': _t('Not Allowed'),
//                            'body': _t(`El cliente ${partner.name}, tiene deuda pendiente de 10 días o más, no puede usar Cashback.`),
//                        });
//                        return;
//                    }
//                }
//
//                if (total_cashback > partner.blocking_amount) {
//                    this.showPopup('ErrorPopup', {
//                        'title': _t('Not Allowed'),
//                        'body': _t(`El valor de pago con Cashback es mayor a la cantidad de Cashback del cliente ${partner.name}, debe ser máximo $${partner.blocking_amount}.`),
//                    });
//                    return;
//                }
//
//                if (!partner.attended_event) {
//                    this.showPopup('ErrorPopup', {
//                        'title': _t('Not Allowed'),
//                        'body': _t('El cliente no asistió al evento, no puede usar Cashback.'),
//                    });
//                    return;
//                }
//
//                if (!partner.active_cashback_limit) {
//                    this.showPopup('ErrorPopup', {
//                        'title': _t('Not Allowed'),
//                        'body': _t('El cliente seleccionado no tiene activo el Cashback, no puede usar este método de Pago'),
//                    });
//                    return;
//                }
//
//                if (total_cashback > 0) {
//                    currentOrder.couponPointChanges = {};
//                }
//            }
//
//            return super.validateOrder(...arguments);
//        }
//    };
//
//    Registries.Component.extend(PaymentScreen, CustomPaymentScreen);
//    return PaymentScreen;
//});
