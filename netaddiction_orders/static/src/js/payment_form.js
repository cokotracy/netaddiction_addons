odoo.define('netaddiction_orders.netaddition_order_payment', function (require) {
    "use strict";
    require('web.dom_ready');
    var core = require('web.core');

    var PaymentForm = require('payment.payment_form');
    PaymentForm.include({
        payEvent: function (ev) {
            var self = this;
            let noteTextarea = $("textarea[id='note']");
            this._rpc({
                route: '/sale/netaddiction/website/data',
                params: {
                    'note': noteTextarea.val(),
                    'order_id': self.options.orderId,
                    'access_token': self.options.accessToken,
                },
            });

            return this._super(ev);
        }
    });

    return PaymentForm;

});
