odoo.define('netaddiction_website.selectCategoryBrand', function (require) {

	var publicWidget = require('web.public.widget');

	publicWidget.registry.selectCategoryBrand = publicWidget.Widget.extend({
		selector: '.js_get_categories',
		start: function () {
			debugger
			var self = this;
			var categoryID = self.$target.data('filterByCategoryId');
	        this._fetch(categoryID);
		},

		_fetch: function (categoryID) {
			debugger
			return this._rpc({
            	route: '/netaddiction_website/get_products_by_category',
            	params: {
                    id: categoryID,
                },
        	}).then(res => {
        		debugger;
        	});
		}
	});
});