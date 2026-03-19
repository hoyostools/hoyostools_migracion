odoo.define("portal_sales_management.rfq_create", ["@web/core/network/rpc_service"],function (require) {
    "use strict";

//    require('web.dom_ready');
//    var ajax = require('web.ajax');
    var jsonrpc = require('@web/core/network/rpc_service');


    //function to search in products in first row [note i will not use theis function as i hide the
    //first row indexed with 0]abd return the closest 10 results in a list
    $('#product-search-input-0').on('keyup',function (e){
        e.preventDefault();
        console.log('ON BLURE')
        var search_word = this.value;
        console.log(search_word);
        jsonrpc('/web/dataset/call_kw/product.product/find_closest_products' ,{
                model: 'product.product',
                method: 'find_closest_products',
                args: [search_word],
                kwargs: {}

            }).then((result,self) => {
                if (result){

                console.log('First on change method : ',result)
                fillDataList(result, 'product-search-input-0')
                }
                else {
                console.log('start calling');
                }
            })
    });

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
    $('#r_add_new_line').on('click', function (e) {
        e.preventDefault();
        var body = document.getElementById("rfq_table");
//        var p_id = document.getElementById("product_id_td");
        var p_description = document.getElementById("product_description_td");
        var unit_price= document.getElementById("unit_price_td");
        var p_qty = document.getElementById("product_qty_td");
        var price_subtotal = document.getElementById("price_subtotal_td");
        var p_delete = document.getElementById("pr_row_delete_td");
        var row = document.createElement("tr");
        row.className = "rfq_row";

        var last_index = String(parseInt(body.lastElementChild.firstElementChild.firstElementChild.id.split('-')[3]) + 1);
        console.log('last index : ', last_index);
            var cell1 = document.createElement("td");
            var cell2 = document.createElement("td");
            var cell3 = document.createElement("td");
            var cell4 = document.createElement("td");

            var cell5 = document.createElement("td");
            var cell6 = document.createElement("td");
            cell2.innerHTML = p_description.innerHTML;
            cell3.innerHTML = unit_price.innerHTML;
            cell5.innerHTML = price_subtotal.innerHTML;


            row.id = "tr-${last_index}";
            cell6.id = "pr_row_delete_td-${last_index}";
            cell1.innerHTML =  `<input class="product-search-input form-control col-md-12 col-sm-4"
                        id="product-search-input-${last_index}"
                               list="dlProducts-${last_index}" required="required" />`;
            cell1.lastElementChild.addEventListener("keyup", function search_for_product(){
                console.log("I'm In Method ", this);
                var search_word = this.value;
                console.log(search_word);
                jsonrpc('/web/dataset/call_kw/product.product/find_closest_products' ,{
                        model: 'product.product',
                        method: 'find_closest_products',
                        args: [search_word],
                        kwargs: {}
                    }).then((result,self) => {
                        if (result){

                        console.log('Second on change method : ',result)
                        fillDataList(result, this.id)
                        }
                        else {
                        console.log('start calling');
                        }
                    });
            });
            cell1.lastElementChild.addEventListener("change", function onchange_product_id(){
                console.log("I'm In onchange Method ", this);
                var product_id = cell1.childNodes[0].value.split('||')[2];
                console.log('product_id',product_id);
                jsonrpc('/web/dataset/call_kw/product.product/find_closest_products' ,{
                        model: 'product.product',
                        method: 'find_related_product_data',
                        args: ["", product_id],
                        kwargs: {}

                    }).then((result2,self) => {
                        if (result2){
                        console.log('find product related data');
                        var cell2inputElement = cell2.querySelector('input[type="text"]');
                        cell2inputElement.value =  result2['name'];
                        var cell3inputElement = cell3.querySelector('input[type="text"]');
                        cell3inputElement.value = result2['price_unit'];
                        }
                        else {
                        console.log('Canot find product related data');
                        }
                    });
            });
//            cell2.innerHTML = p_description.innerHTML;
//            cell3.innerHTML = unit_price.innerHTML;
            cell4.innerHTML = p_qty.innerHTML;
            cell4.lastElementChild.addEventListener("change", function onchange_product_qty(){
                console.log("I'm In onchange qty Method ", this);
                console.log("P unit val ",cell3.querySelector('input[type="text"]').value );
                var cell5inputElement = cell5.querySelector('input[type="text"]');
                cell5inputElement.value = parseFloat(cell3.querySelector('input[type="text"]').value) * parseFloat(cell4.querySelector('input[type="text"]').value);
            });
//            cell5.innerHTML = price_subtotal.innerHTML;


            cell6.innerHTML = p_delete.innerHTML;
            cell6.addEventListener("click", function delete_line(){
                console.log("deleted row: ", this);
                $(this).closest('tr').remove(); });


            row.appendChild(cell1);
            row.appendChild(cell2);
            row.appendChild(cell3);
            row.appendChild(cell4);
            row.appendChild(cell5);
            row.appendChild(cell6);



        body.appendChild(row);
        var lines = document.getElementsByClassName("product-search-input");
        console.log("All Lines", lines);

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
        var table = document.getElementById("rfq_table");
        for (var i = 2; i < table.rows.length ;i++) {
            var row = table.rows[i];
            console.log('row ..',row)
//            console.log('row child nodes..',row.cells[0].childNodes)
//            console.log('row child node 0 ..',row.cells[0].childNodes[0].value)
//            console.log('row child node 1 ..',row.cells[0].childNodes[1].value)
            if (row.cells[0].childNodes.length == 3){
                var x_val = row.cells[0].childNodes[1].value
                }
            else{
                var x_val = row.cells[0].childNodes[0].value
            }
            var chars = x_val.split('||');
            console.log('chars product name',chars);
            if (chars.length < 3){
            console.log('chars.length',chars.length);
                let text = "Warning!\n line#"+i+" have not valid product \n please contact with responsible employee (To add the product)";
                  if (alert(text) == true) {
                    return;
                  } else {
                    return;
                  }
            }
            var product_id = parseInt(chars[2]);
            console.log('p id',chars[2])
            var product_description_variants = row.cells[1].children[0].value;
            var product_unit_price = parseFloat(row.cells[2].children[0].value);
            var product_qty = parseFloat(row.cells[3].children[0].value);
            order_lines.push({'product_id':product_id,'name':product_description_variants,'price_unit':product_unit_price,'product_uom_qty':product_qty})
        }
        console.log(vals)
        jsonrpc('/web/dataset/call_kw/sale.order/action_prepare_vals' ,{
                model: 'sale.order',
                method: 'action_prepare_vals',
                args: [vals],
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
});
