odoo.define('netaddiction_website_stock_notify.notify', function (require) {
  'use strict';

  var publicWidget = require('web.public.widget');
  var ajax = require('web.ajax');
  var session = require('web.session');



  publicWidget.registry.websiteStockNotification = publicWidget.Widget.extend({
    selector: '.o_product_notify',
    events: {
      'click .submit-notify': '_onNotificationButtonClick',
    },

    _onNotificationButtonClick: function (ev) {
      ev.preventDefault();
      var self = this;
      var email = this.$('#email').val();
      var validRegex = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
      var $parent = $(ev.target).closest('.js_product');
      var product_id = $parent.find('.product_id').val();

      this.$('.o_notify_message').addClass('d-none');
      if (email.length > 0 && email.match(validRegex)) {
        ajax.jsonRpc('/shop/product/stock/notification', 'call', {
          'email': email,
          'product_id': product_id,
        }).then(function (result) {
          if (["duplicate", "error"].includes(result.status)) {
            self.$('.o_notify_alert_message').html(result.message).removeClass('d-none');
            if (result.status === "duplicate") {
              self.$(ev.target).prop("disabled", true);
              self.$('#email').prop("disabled", true);
            }
            setTimeout(() => {
              self.$('.o_notify_alert_message').addClass('d-none').html("");
            }, 5000);
          } else {
            self.$('.o_notify_message').html(result.message).removeClass('d-none');
            self.$(ev.target).prop("disabled", true);
            self.$('#email').prop("disabled", true);
            setTimeout(() => {
              self.$('.o_notify_message').addClass('d-none').html("");
            }, 5000);
          }
        })
      } else {
        this.$('#email').val(" ");
        this.$('.o_notify_alert_message').html("Inserisci un indirizzo e-mail valido.").removeClass('d-none');
        setTimeout(() => {
          this.$('.o_notify_alert_message').addClass('d-none').html("");
        }, 5000);
      }
    },
  });
});