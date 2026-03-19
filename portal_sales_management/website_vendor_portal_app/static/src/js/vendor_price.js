//odoo.define('website_cancel_order_app.cancel_order',function(require){
//"use strict";
	$(document).ready(function() {
//		var ajax=require('web.ajax');
//		var core=require('web.core');
//		var _t=core._t;
		var quote_ids;
		var order_ids;
		$('.js_vendor').click(function(){
			quote_ids = $(this).attr('id')
		})
		$(".submit_btn").click(function(){
			var vendor_date =  $('#delivery_date').val();
			var date = new Date(vendor_date);
			var delivery_date = date.getMonth() + 1 +"/"+ date.getDate()+"/"+ date.getFullYear()
			var description = $('#description').val();
			var vendor_price = $('#vendor_price').val();
			var modal_quantity = $('#modal_quantity').val();
			var old_qty = $('#old_qty').val();
			order_ids = $('.order_id').val();

			if (old_qty < modal_quantity){
				alert("La cantidad ingresada debe ser menor o igual a " + old_qty);
			}
			var dataitem={
				date: delivery_date,
				description: description,
				price : vendor_price,
				qty: modal_quantity,
			};
			$.ajax({
				url: '/my/quotes/'+quote_ids+'/vendor_price',
				type: "POST",
				datatype: 'http',
				data: dataitem,
				success: function ()
				{
					// window.location.href="/my/quote/";
					var origin = window.location.origin;
					var origin = origin + "/my/quote/"+order_ids;
					window.location.replace(origin);

					}
				});
		});
	});
//});