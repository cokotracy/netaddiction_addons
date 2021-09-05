odoo.define('website_all_in_one.odoo_website_giftwrap', function(require) {
	"use strict";

	var core = require('web.core');
	var _t = core._t;
	var ajax = require('web.ajax');
	var rpc = require('web.rpc');

	$(document).ready(function() {
		var oe_website_sale = this;
		
		var $giftwrap = $("#row_data");

		$('.item_image').each(function(){

			$('.raghav').removeClass('raghav');
			$(this).on('click',function () {
				if ( $(this).hasClass('raghav') )
				{
					$('.raghav').removeClass('raghav');
				}
				else{
					$('.raghav').removeClass('raghav');
					$(this).addClass('raghav');
				}
			});
		});

		$('#giftwrapbutton').on('click', function() {
				var notes = $("#notes").val();
				var product = $(".raghav").data('id');

				ajax.jsonRpc('/shop/cart/giftwrap', 'call', {
					'notes': notes,
					'product':product,
				}).then(function (notes) {
					rpc.query({
					model: 'website',
					method: 'get_gift_product',
					args: [product],
					}).then(function (data) {
						location.reload();
					});
					
				});
								
				
			});


	});
});;
