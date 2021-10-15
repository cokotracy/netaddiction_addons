odoo.define('netaddiction_theme_rewrite.custom_button_buy_now', function (require) {
  'use strict';

  var publicWidget = require('web.public.widget');
  publicWidget.registry.WebsiteSale.include({
    events: _.extend({}, publicWidget.registry.WebsiteSale.prototype.events, {
      'click #add_to_cart, #buy_now, #products_grid .o_wsale_product_btn .a-submit': '_onClickAdd',
    }),
    /**
     * @private
     * @param {MouseEvent} ev
     */
    _onClickAdd: function (ev) {
      ev.preventDefault();
      let product_id = null
      product_id = ev.target.dataset.product
      if (product_id)
        document.location.href = `/shop/payment?buynow=${product_id}`
      else
        return this._super.apply(this, arguments);
    },
  });

});
