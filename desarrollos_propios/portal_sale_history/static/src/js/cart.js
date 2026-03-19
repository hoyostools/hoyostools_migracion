/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";

publicWidget.registry.PortalQuickAdd = publicWidget.Widget.extend({

    selector: "#portal_table",

    events: {
        "click .add_to_cart_btn": "_addToCart",
    },

    async _addToCart(ev) {

        ev.preventDefault();

        const btn = ev.currentTarget;
        const product_id = btn.dataset.productId;

        const qtyInput = btn.closest("td").querySelector(".add_qty");
        const qty = qtyInput ? qtyInput.value : 1;

        try {

            const data = await jsonrpc("/shop/cart/update_json", {
                product_id: parseInt(product_id),
                add_qty: parseInt(qty),
            });

            // actualizar contador carrito

            if (data.cart_quantity !== undefined) {

                const cartQty = document.querySelector('.my_cart_quantity');

                if (cartQty) {
                    cartQty.textContent = data.cart_quantity;

                    if (data.cart_quantity > 0) {
                        cartQty.classList.remove('d-none');
                    } else {
                        cartQty.classList.add('d-none');
                    }
                }
            }

        } catch (error) {

            window.alert("No se pudo agregar el producto al carrito.");

        }

    }

});

publicWidget.registry.FilterProducts = publicWidget.Widget.extend({

    selector: ".card",  // puedes hacerlo más específico

    events: {
        "change #filter_category": "_onChangeCategory",
    },

    async _onChangeCategory(ev) {

        const brand = ev.currentTarget.value;

        const data = await jsonrpc('/my/filter_products', {
            product_brand_id: brand
        });

        const tbody = document.querySelector("#new_products_tbody");

        tbody.innerHTML = "";

        data.forEach(product => {

            const row = `
                <tr class="product-row">

                    <td style="width:70px">
                        <img src="${product.image}"
                             style="width:50px;height:50px;object-fit:cover;"/>
                    </td>

                    <td>${product.name}</td>

                    <td>${product.price}</td>

                    <td>
                        <div class="d-flex gap-2">
                            <input type="number" class="form-control text-center add_qty" value="1" min="1" style="width:60px"/>
                            <button class="btn btn-sm btn-primary add_to_cart_btn" data-product-id="${product.id}">
                                <i class="fa fa-shopping-cart"></i>
                            </button>
                        </div>
                    </td>

                </tr>
            `;

            tbody.insertAdjacentHTML("beforeend", row);
        });

    }

});

