odoo.define('netaddiction_theme_rewrite.custom_popup_add_to_cart', function (require) {
  'use strict';
  var publicWidget = require('web.public.widget');
  var productsRecentlyViewedSnippet = publicWidget.registry.productsRecentlyViewedSnippet
  var wSaleUtils = require('website_sale.utils');

  productsRecentlyViewedSnippet.include({
    _onAddToCart: function (ev) {
      var self = this;
      var $card = $(ev.currentTarget).closest('.card');
      this._rpc({
          route: "/shop/cart/update_json",
          params: {
              product_id: $card.find('input[data-product-id]').data('product-id'),
              add_qty: 1
          },
      }).then(function (data) {
          wSaleUtils.updateCartNavBar(data);
          var $navButton = $('header .o_wsale_my_cart').first();
          var fetch = self._fetch();
          var animation = wSaleUtils.animateClone($navButton, $(ev.currentTarget).parents('.o_carousel_product_card'), 25, 40);
          Promise.all([fetch, animation]).then(function (values) {
              self._render(values[0]);
          });
          var $button = $('#custom_popup_add_to_cart');
          if($button != null){
            var $prod_image = $card.find('.o_carousel_product_card_img_top').attr('src');
            var $prod_name = $card.find('.product_name').text();
            $('#modal_message .modal-body .img_custom_add_to_cart').html(`<img src="${$prod_image}"/>`);
            $('#modal_message .modal-body .text_custom_add_to_cart').html(`<p class="h5"><span class="text-primary">${$prod_name}</span><br/><br/>Prodotto aggiunto al carrello!</p>`);
            $button.click();
            setTimeout(() => {
              $('.close_modal_custom_add_to_cart').click()
            }, 2500);
            
          }
        });
    },
  })

  return productsRecentlyViewedSnippet
})