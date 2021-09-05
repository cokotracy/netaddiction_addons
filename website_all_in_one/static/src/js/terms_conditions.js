odoo.define('website_all_in_one.terms_conditions', function(require) {
    "use strict";
    var core = require('web.core');
    var _t = core._t;

    var ajax = require('web.ajax');
    $(document).ready(function() {
	    var oe_website_sale = this;
		
		var $terms = $("#terms_conditions");
		$('.terms-conditions').parents(".oe_website_sale").find("form button.btn-primary").attr('disabled', true);
		$terms.click(function () {
			//check if checkbox is checked
			if ($(this).is(':checked')) {
				$('.oe_website_sale form button.btn-primary').removeAttr('disabled'); //enable button
				
			} else {
				$('.oe_website_sale form button.btn-primary').attr('disabled', true); //disable button
			}
		});
		
        
        
    });
});;
