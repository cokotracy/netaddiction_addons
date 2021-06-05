odoo.define('netaddiction_website.snippets.options', function (require) {
	var options = require('web_editor.snippets.options');
	var wUtils = require('website.utils');

	options.registry.selectBrandCategory = options.Class.extend({
		start: function () {
			    var self = this;
				var def = this._rpc({
	            model: 'product.public.category',
	            method: 'search_read',
	            args: [wUtils.websiteDomain(this), ['name']],
        		}).then(categories => {
            		var allCategoryEl = this.el.querySelector('[data-filter-by-category-id="0"]');
            		var menuEl = allCategoryEl.parentNode;
            		for (const category of categories) {
		                let el = allCategoryEl.cloneNode();
		                el.dataset.filterByCategoryId = category.id;
		                el.textContent = category.name;
		                menuEl.appendChild(el);
            		}
        		});

        	return Promise.all([this._super.apply(this, arguments), def]);

		},

		filterByCategoryId: function (previewMode, value, $opt) {
			value = parseInt(value);
        	this.$target.attr('data-filter-by-category-id', value).data('filterByCategoryId', value);
        	this.trigger_up('widgets_start_request', {
            editableMode: true,
            $target: this.$target,
        });
		},
	});
});