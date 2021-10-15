odoo.define('netaddiction_theme_rewrite.custom_button_buy_now', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    require('website_sale.website_sale');


    publicWidget.registry.WebsiteSale.include({
        events: _.extend({
            'click #add_to_cart, #buy_now, #products_grid .o_wsale_product_btn .a-submit': 'async _onClickAdd',
        }),
        /**
         * @private
         * @param {MouseEvent} ev
         */
        _onClickAdd: function (ev) {
            ev.preventDefault();
            console.log('CIAONEEEEEE')
            this.isBuyNow = $(ev.currentTarget).attr('id') === 'buy_now';
            return this._handleAdd($(ev.currentTarget).closest('form'));
        },
    });

});
  