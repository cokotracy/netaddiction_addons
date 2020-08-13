odoo.define('netaddiction_website.mainPage', function (require) {
	var publicWidget = require('web.public.widget');


	publicWidget.registry.productsMostlySold = publicWidget.registry.productsRecentlyViewedSnippet.extend({
		selector: '.s_products_mostly_sold',
		start: function () {
			this._fetch();
		},
		_fetch: function () {
			return this._rpc({
            route: '/netaddiction_website/mostly_sold',
        }).then(function(abc) {
        	var products = res['products'];
            return res;
        });
		}
	});
});

