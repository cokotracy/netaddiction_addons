odoo.define('netaddiction_website.productsMostlySold', function (require) {
    var publicWidget = require('web.public.widget');

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

    publicWidget.registry.productsPriceRangeSlider = publicWidget.Widget.extend({
        selector: '.product_price_range_slider',
        events: {
            'input input': '_onPriceRangeChange',
            'click .price_filter': '_onClickApplyFilter',
        },
        start: function() {
            this._super.apply(this, arguments);
            this._updatePriceRange();
        },

        // ---------------
        // Helpers
        // ---------------

        /**
         * update price range.
         * @private
         */
        _updatePriceRange: function() {
            var slide1 = parseFloat(this.$('#slide1').val());
            var slide2 = parseFloat(this.$('#slide2').val());
            if( slide1 > slide2 ){ var tmp = slide2; slide2 = slide1; slide1 = tmp; }
            var text = "$ " + slide1 + " - $" + slide2;
            this.$('.rangeValues').text(text);
        },
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * Call debounced method when price range change.
         * @private
         * @param {Event} ev
         */
        _onPriceRangeChange: function(ev) {
            this._updatePriceRange();
        },

        /**
         * @private
         * @param {Event} ev
         */
        _onClickApplyFilter: function(ev) {
            ev.preventDefault();
            var oldurl = $(ev.currentTarget).attr('href');
            oldurl += (oldurl.indexOf("?")===-1) ? "?" : "";
            var pricemin = this.$('#slide1').val();
            var pricemax = this.$('#slide2').val();
            window.location = oldurl + '&' + 'price_min' + '=' + encodeURIComponent(pricemin) + '&' + 'price_max' + '=' + encodeURIComponent(pricemax);
        },

    });
});

