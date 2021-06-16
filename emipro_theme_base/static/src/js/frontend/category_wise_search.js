odoo.define('emipro_theme_base.category_wise_search', function(require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var productsSearchBar = publicWidget.registry.productsSearchBar
    const { qweb } = require('web.core');

    productsSearchBar.include({
    	xmlDependencies: productsSearchBar.prototype.xmlDependencies.concat(
        	['/emipro_theme_base/static/src/xml/advanced_search.xml']
    	),
        events: _.extend({}, productsSearchBar.prototype.events, {
            'click .ept-category-a': 'change_category',
        }),
        change_category: function() {
            if (this.$input.val()){
                this._onInput();
            }
        },
        _fetch: function () {
            return this._rpc({
                route: '/shop/products/autocomplete',
                params: {
                    'term': this.$input.val(),
                    'options': {
                        'order': this.order,
                        'limit': this.limit,
                        'display_description': this.displayDescription,
                        'display_price': this.displayPrice,
                        'max_nb_chars': Math.round(Math.max(this.autocompleteMinWidth, parseInt(this.$el.width())) * 0.22),
                        'cat_id' : this.$el.find('.te_advanced_search_div .dropdown-menu a.dropdown-item.active').attr('value'),
                        'search_in' : this.$el.find('.te_advanced_search_div .dropdown-menu a.dropdown-item.active').attr('search_in') || false
                    },
                },
            });
        },
        // Render the category and blogs
        _render: function (res) {
			var $prevMenu = this.$menu;
			this.$el.toggleClass('dropdown show', !!res);
			if (res) {
				var products = res['products'];
				var categories = res['categories'];
				var blogs = res['blogs'];
				console.log(res['blogs_count'])
				this.$menu = $(qweb.render('website_sale.productsSearchBar.autocomplete', {
					products: products,
					categories:categories,
					blogs:blogs,
					hasMoreProducts: products && products.length < res['products_count'],
					hasMoreBlogs: blogs && blogs.length < res['blogs_count'],
					currency: res['currency'],
					term:this.$input.val(),
					widget: this,
				}));
				this.$menu.css('min-width', this.autocompleteMinWidth);
				this.$el.append(this.$menu);
			}
			if ($prevMenu) {
				$prevMenu.remove();
			}
    	},
    });
});