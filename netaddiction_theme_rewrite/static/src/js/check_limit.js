odoo.define('netaddiction_theme_rewrite.check_order_limit', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');

    publicWidget.registry.check_order_limit = publicWidget.Widget.extend({
        selector: '#wrapwrap',
        init: function () {
            this._super.apply(this, arguments);
        },
        events:{
            'click #order_limit_net': '_checkLimit',
        },
        _checkLimit: function (ev) {
            ev.preventDefault();
            this._rpc({
                route: "/shop/cart/check_limit_order",
            }).then(function (data) {
                if(data != null){
                    if(data['order_limit'] != null)
                        return alert('Non Puoi ordinare più di '+data['order_limit']+' unità per questo prodotto: '+data['product_name']);
                    else if(data['order_limit_total'] != null)
                        return alert('Questo prodotto non è più vendibile: '+data['product_name']);
                }
                else
                    return window.location = '/shop/checkout?express=1';
            });
        },
    });
});


odoo.define('netaddiction_theme_rewrite.limit_product_payment', function(require) {
    "use strict";
    var PaymentForm = require('payment.payment_form');
    
    require('web.dom_ready');
    
    PaymentForm.include({
        events: _.extend({
            "submit": "onSubmit",
        }),
        onSubmit: function(ev) {
            ev.stopPropagation();
            ev.preventDefault();

            this._rpc({
                route: "/shop/cart/check_limit_order",
            }).then(function (data) {
                if(data != null){
                    if(data['order_limit'] != null)
                        return alert('Non Puoi ordinare più di '+data['order_limit']+' unità per questo prodotto: '+data['product_name']);
                    else if(data['order_limit_total'] != null)
                        return alert('Questo prodotto non è più vendibile: '+data['product_name']);
                }
                else{
                    var button = $(ev.target).find('*[type="submit"]')[0]
                    if (button.id === 'o_payment_form_pay') {
                        return this.payEvent(ev);
                    } else if (button.id === 'o_payment_form_add_pm') {
                        return this.addPmEvent(ev);
                    }
                    return;
                }
            });
        }
    });
});