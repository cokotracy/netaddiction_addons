odoo.define('netaddiction_theme_rewrite.VariantMixin', function (require) {
  'use strict';

  var VariantMixin = require('website_sale_stock.VariantMixin');
  var ajax = require('web.ajax');
  var core = require('web.core');
  var QWeb = core.qweb;
  var xml_load = ajax.loadXML('/website_sale_stock/static/src/xml/website_sale_stock_product_availability.xml', QWeb);
  var xml_load_label = ajax.loadXML('/netaddiction_theme_rewrite/static/src/xml/template_label.xml', QWeb);
  VariantMixin.xmlDependencies = ['/netaddiction_theme_rewrite/static/src/xml/template_label.xml'];

  VariantMixin._onChangeCombinationStock = function (ev, $parent, combination) {
    var product_id = 0;
    // needed for list view of variants
    if ($parent.find('input.product_id:checked').length) {
      product_id = $parent.find('input.product_id:checked').val();
    } else {
      product_id = $parent.find('.product_id').val();
    }
    var isMainProduct = combination.product_id &&
      ($parent.is('.js_main_product') || $parent.is('.main_product')) &&
      combination.product_id === parseInt(product_id);

    if (!this.isWebsite || !isMainProduct) {
      return;
    }

    var qty = $parent.find('input[name="add_qty"]').val();

    $parent.find('#add_to_cart').removeClass('out_of_stock');
    $parent.find('#buy_now').removeClass('out_of_stock');

    this._rpc({
      route: "/get_product_from_id",
      params: {
        product_id: combination.product_id,
      },
    }).then(function (data) {
      if (data != null) {
        var $exposed_out_date = $('#out_date_converted');
        if($exposed_out_date != null){
          var date = new Date(data.out_date);
          var exposed_date = date.toLocaleString('it-it', {month: 'long',}) + ' ' + date.getFullYear();
          $exposed_out_date.text(exposed_date)
        }

        xml_load_label.then(function () {
          var $infoLabel = $(QWeb.render(
            'netaddiction_theme_rewrite.product_label_info',
            data
          ));
          $('div#label_info_product').html($infoLabel);

          var $notifyField = $(QWeb.render(
            'netaddiction_theme_rewrite.product_notify',
            data
          ));
          $('div#notify-my-mail').html($notifyField);
        });

        if (data.qty_sum_suppliers > 0 || data.qty_available_now > 0) return;
        if (data.inventory_availability === 'never' && (data.out_date !== "" || new Date(data.out_date) > new Date())) return;
        if (combination.product_type === 'product' && ['always', 'threshold'].includes(combination.inventory_availability)) {
          combination.virtual_available -= parseInt(combination.cart_qty);
          if (combination.virtual_available < 0) {
            combination.virtual_available = 0;
          }
          // Handle case when manually write in input
          if (qty <= combination.qty_available_now) {
            var $input_add_qty = $parent.find('input[name="add_qty"]');
            qty = combination.virtual_available || 1;
            $input_add_qty.val(qty);
          }
          if (qty >= combination.qty_available_now) {
            $parent.find('#add_to_cart').removeClass('disabled out_of_stock');
            $parent.find('#buy_now').removeClass('disabled out_of_stock');
          } else {
            $('a#buy_now').each(function () {
              this.removeEventListener("click", {});
            })
            $parent.find('#add_to_cart').addClass('disabled out_of_stock');
            $parent.find('#buy_now').addClass('disabled out_of_stock');
          }
        }
      }

      xml_load.then(function () {
        $('.oe_website_sale')
          .find('.availability_message_' + combination.product_template)
          .remove();

        var $message = $(QWeb.render(
          'website_sale_stock.product_availability',
          combination
        ));
        $('div.availability_messages').html($message);
      });
    });
  };

  return VariantMixin;
});
