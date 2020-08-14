odoo.define('netaddiction_website.mainPage', function (require) {
	var publicWidget = require('web.public.widget');


	publicWidget.registry.productsMostlySold = publicWidget.registry.productsRecentlyViewedSnippet.extend({
		selector: '.s_products_mostly_sold',
		start: function () {
			this._fetch().then(this._render.bind(this));
		},
		_fetch: async function () {
			var self =this;
			debugger;
			return await this._rpc({
            route: '/netaddiction_website/mostly_sold',
        }).then(function(res) {
        	debugger;
        	// var products = res['products'];
            return res;
        });
		}
	});
});

