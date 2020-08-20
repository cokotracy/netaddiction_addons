odoo.define('netaddiction_website.productBestSeller', function (require) {
var publicWidget = require('web.public.widget');
// var recentlyViewed = require('website_sale.recently_viewed');
var config = require('web.config');
var core = require('web.core');

var qweb = core.qweb;


publicWidget.registry.BestSeller = publicWidget.registry.productsRecentlyViewedSnippet.extend({
    selector: 'div.o_best_seller',
    xmlDependencies: ['/netaddiction_website/static/src/xml/netaddiction_template.xml'],
    disabledInEditableMode: false,

    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);
        this.uniqueId = _.uniqueId('o_carousel_most_sale_products_');
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _fetch: function () {
        return this._rpc({
            route: '/netaddiction_website/mostly_sold',
        }).then(res => {
            var products = res['products'];

            // In edit mode, if the current visitor has no recently viewed
            // products, use demo data.
            if (this.editableMode && (!products || !products.length)) {
                return {
                    'products': [{
                        id: 0,
                        website_url: '#',
                        display_name: 'Product 1',
                        price: '$ <span class="oe_currency_value">750.00</span>',
                    }, {
                        id: 0,
                        website_url: '#',
                        display_name: 'Product 2',
                        price: '$ <span class="oe_currency_value">750.00</span>',
                    }, {
                        id: 0,
                        website_url: '#',
                        display_name: 'Product 3',
                        price: '$ <span class="oe_currency_value">750.00</span>',
                    }, {
                        id: 0,
                        website_url: '#',
                        display_name: 'Product 4',
                        price: '$ <span class="oe_currency_value">750.00</span>',
                    }],
                };
            }

            return res;
        });
    },
    /**
     * @private
     */
    _render: function (res) {
        var products = res['products'];
        var mobileProducts = [], webProducts = [], productsTemp = [];
        _.each(products, function (product) {
            if (productsTemp.length === 4) {
                webProducts.push(productsTemp);
                productsTemp = [];
            }
            productsTemp.push(product);
            mobileProducts.push([product]);
        });
        if (productsTemp.length) {
            webProducts.push(productsTemp);
        }

        this.mobileCarousel = $(qweb.render('netaddiction_website.bestSellerViewed', {
            uniqueId: this.uniqueId,
            productFrame: 1,
            productsGroups: mobileProducts,
        }));
        this.webCarousel = $(qweb.render('netaddiction_website.bestSellerViewed', {
            uniqueId: this.uniqueId,
            productFrame: 4,
            productsGroups: webProducts,
        }));
        this._addCarousel();
        this.$el.toggleClass('d-none', !(products && products.length));
    },
    /**
     * Add the right carousel depending on screen size.
     * @private
     */
    _addCarousel: function () {
        var carousel = config.device.size_class <= config.device.SIZES.SM ? this.mobileCarousel : this.webCarousel;
        this.$el.find('.o_best_seller_slider').html(carousel);
    },
});
});