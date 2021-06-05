odoo.define('website_stock_notify.notify', function (require) {
'use strict';

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

    publicWidget.registry.websiteStockNotification = publicWidget.Widget.extend({
        selector: '.o_product_notify',
        events: {
            'click .submit-notify': '_onNotificationButtonClick',
        },

        _onNotificationButtonClick: function (ev) {
            ev.preventDefault();
            var self = this;
            var email = this.$('#email').val();
            var $parent = $(ev.target).closest('.js_product');
            var product_id = $parent.find('.product_id').val();
            this.$('.o_notify_alret_message').toggleClass('d-none', email.length > 0);
            this.$('.o_notify_message').addClass('d-none');
            if (email) {
                ajax.jsonRpc('/shop/product/stock/notification', 'call', {
                    'email': email,
                    'product_id': product_id,
                }).then(function (result) {
                    self.$('#email').val(" ");
                    self.$('.o_notify_message').removeClass('d-none');
                })
            }
        },
    });
});