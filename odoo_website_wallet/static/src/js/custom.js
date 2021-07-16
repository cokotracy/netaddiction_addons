odoo.define('odoo_website_wallet.odoo_website_wallet', function(require) {
    "use strict";
    var core = require('web.core');
    var _t = core._t;

    var ajax = require('web.ajax');
    $(document).ready(function() {
	    var oe_website_sale = this;
		$('#not_wallet').click(function () {
			ajax.jsonRpc('/shop/payment/wallet', 'call', {
				'wallet':  false,
			}).then(function (wallet) {
				location.reload();
			});
		});

		$('#wallet_checked').click(function () {
			ajax.jsonRpc('/shop/payment/wallet', 'call', {
				'wallet': true,
			}).then(function (wallet) {
				location.reload();
			});
		});
    });
});;
