/** @odoo-module **/

    import { registry } from "@web/core/registry";
    import { jsonrpc } from "@web/core/network/rpc_service";
    import { Dialog } from "@web/core/dialog/dialog";
    import { _t } from "@web/core/l10n/translation";

    //    this function is used to create dataList of matched products and append it to product input
    function fillDataList(search_list, id) {
        console.log('IN FIl ', document);
        var inputContainer = document.getElementById(String(id));
        var list_id = String('dlProducts-'+ String(id).split('-')[3]);
        var dl = document.getElementById(list_id);
        var len = search_list.length;
        console.log('id : ', list_id, dl);

        if (!dl){
             dl = document.createElement('datalist');
             dl.id = list_id;
        }
        else{
        document.getElementById(list_id).innerHTML = '';

            console.log('dl empty');
        }
        for (var i=0; i < len; i += 1) {
            var option = document.createElement('option');
            option.value = search_list[i]['internal_reference']+'|| '+search_list[i]['name']+'|| '+search_list[i]['id'];
            dl.appendChild(option);
            console.log("DL: ", dl);
        }

        inputContainer.appendChild(dl);
        console.log("input with data list", inputContainer);

    };

    //    this the main buseness
    $('#r_add_new_line').on('click', function (ev) {
       var self = this;
        var ptype = $(ev.currentTarget).attr('data-type');


        jsonrpc('/portal_sales/add/row', {
            'type': ptype,
        }).then((data) => {
            var $tableBody = $(ev.currentTarget).closest('.card-body').find('table tbody');
            $tableBody.find('.select2').select2('destroy');
            $tableBody.append(data.data);

            $tableBody.find('.select2').select2({
                theme: 'bootstrap4',
                width: '100%',
                dropdownCssClass: 'bootstrap-select',
                containerCssClass: 'bootstrap-select-container',
            });

            $tableBody.on('click', '#pr_row_delete', function(ev) {
                //self.remove_added_row(ev);
                $(this).closest('tr').remove();
            });
            $tableBody.on('change', '#product_id', function () {
                var $row = $(this).closest('tr');
                var productId = $(this).val();
                var pricelist_id = $('#pricelist_id').val();

                console.log("Cambiando producto, ID:", productId);

                if (productId){
                    // Llamada para obtener datos relacionados del producto
                    jsonrpc('/web/dataset/call_kw/product.product/find_closest_products', {
                        model: 'product.product',
                        method: 'find_related_product_data',
                        args: ["", productId, pricelist_id],
                        kwargs: {}
                    }).then((result) => {
                        if (result) {
                            console.log('Datos relacionados del producto encontrados:', result);

                            // Actualizar campos en la fila
                            $row.find('#product_description').val(result['name']);
                            $row.find('#price_unit').val(result['price_unit']);

                            // Recalcular subtotal automáticamente
                            var quantity = parseFloat($row.find('#product_qty').val()) || 1;
                            var totalPrice = result['price_unit'] * quantity;
                            $row.find('#price_subtotal').val(totalPrice.toFixed(2));
                        } else {
                            console.log('No se encontraron datos relacionados del producto');
                        }
                    });
                }


            });
             $tableBody.on('change', '#product_qty', function () {
                var $row = $(this).closest('tr'); // Obtenemos la fila actual
                var $unitPriceInput = $row.find('#price_unit'); // Input del precio unitario (cell3)
                var $qtyInput = $row.find('#product_qty'); // Input de cantidad (cell4)
                var $totalPriceInput = $row.find('#price_subtotal'); // Input de precio total (cell5)

                // Obtener los valores
                var unitPrice = parseFloat($unitPriceInput.val()) || 0; // Valor de precio unitario
                var quantity = parseFloat($qtyInput.val()) || 0; // Valor de cantidad

                // Calcular el precio total
                var totalPrice = unitPrice * quantity;

                // Actualizar el campo de precio total
                $totalPriceInput.val(totalPrice.toFixed(2));

                console.log("Cantidad cambiada, nuevo total:", totalPrice);
             });

             // **Nuevo: Evento para cambiar precio unitario**
            $tableBody.on('change', '#price_unit', function () {
                var $row = $(this).closest('tr');
                var $unitPriceInput = $(this);
                var $qtyInput = $row.find('#product_qty');
                var $totalPriceInput = $row.find('#price_subtotal');

                var unitPrice = parseFloat($unitPriceInput.val()) || 0;
                var quantity = parseFloat($qtyInput.val()) || 0;

                var totalPrice = unitPrice * quantity;
                $totalPriceInput.val(totalPrice.toFixed(2));

                console.log("Precio unitario cambiado, nuevo total:", totalPrice);
            });

        })

     });

     //  Selector for handel deleting row
    $('#pr_row_delete').on('click', function (e) {
        e.preventDefault();
        console.log('dddd')
        $(this).closest('tr').remove();
    });

    //  Selector for handel creating New QUOTATION
    $('#create_quotation_data').on('click',function(e) {
        e.preventDefault();
        var date_order = $('#date_order').val()
        var partner_id = $('#partner_id').val();
        var pricelist_id = $('#pricelist_id').val();
        if (! partner_id){
                let text = "Warning! You can\'t create quotation without customer";
                  if (alert(text) == true) {
                    return;
                  } else {
                    return;
                  }
            }



        var order_lines = [];
        var vals = [{'date_order':date_order,'partner_id':partner_id,'pricelist_id':pricelist_id},order_lines];
        $('#rfq_table tr').each(function (index, row) {
            // Asegurarse de que la fila no esté vacía
            var $row = $(row);
            if ($row.find('td').length > 0) {
                // Obtener el valor del producto seleccionado en la celda del producto
                var product_id = $row.find('select[name="product_id"]').val(); // Valor del producto
                var product_description_variants = $row.find('input[name="product_description"]').val(); // Descripción
                var product_unit_price = parseFloat($row.find('input[name="price_unit"]').val()) || 0; // Precio unitario
                var product_qty = parseFloat($row.find('input[name="product_qty"]').val()) || 1; // Cantidad

                // Validar si el producto es válido
                if (!product_id || !product_unit_price || !product_qty) {
                    alert("Warning!\n Line #" + (index + 1) + " is incomplete. Please ensure product, price, and quantity are filled.");
                    return;
                }

                // Agregar línea a order_lines
                order_lines.push({
                    'product_id': parseInt(product_id),
                    'name': product_description_variants,
                    'price_unit': product_unit_price,
                    'product_uom_qty': product_qty
                });
            }
        });
        console.log(vals)
        jsonrpc('/web/dataset/call_kw/sale.order/action_prepare_vals' ,{
                model: 'sale.order',
                method: 'action_prepare_vals',
                args: ['',vals],
                kwargs: {}
            }).then((result,self) => {
                if (result){
                var ptrn = 'my/quotes/create';
                var base_url = window.location.href.toString();
                var str2 = base_url.replace(ptrn, "my/quotes");
                window.location.href = str2
                }
                else {console.log('error',);window.alert('You Can\'t Create Quotation');}
            })

    });