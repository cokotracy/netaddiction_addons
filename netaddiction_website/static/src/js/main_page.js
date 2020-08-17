odoo.define('netaddiction_website.productsMostlySold', function (require) {
	var publicWidget = require('web.public.widget');
	var core = require('web.core');
	var config = require('web.config');

	var qweb = core.qweb;


	publicWidget.registry.productsMostlySold = publicWidget.registry.productsRecentlyViewedSnippet.extend({
		selector: '.s_products_mostly_sold',
		
		_fetch: async function () {
			var self =this;
			return await this._rpc({
            	route: '/netaddiction_website/mostly_sold',
        	}).then(function(res) {
            	return res;
        	});
        	return this._super.apply(this, arguments);
		},
		_render: function (res) {
			this.$el.find('section').toggleClass('d-none', !res);
			return this._super.apply(this,arguments);
		},
	});
});

