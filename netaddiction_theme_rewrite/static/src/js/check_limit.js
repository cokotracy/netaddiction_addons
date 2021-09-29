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
                    var message;
                    if(data['order_limit'] != null)
                        message = '<span class="text-primary mb-3 d-block">Non Puoi ordinare più di '+data['order_limit']+' unità per questo prodotto:</span> '+data['product_name'];
                    else if(data['order_limit_total'] != null)
                        message = '<span class="text-primary mb-3 d-block">Questo prodotto non è più vendibile:</span> '+data['product_name'];
                    else if(data.out_of_stock)
                        message = '<span class="text-primary mb-3 d-block">Questo prodotto non è più disponibile:</span> '+data['product_name'];

                    if (message != null){
                        var button = document.querySelector('#error_modal');
                        document.querySelector('#modal_message .modal-body .img-error').innerHTML = '<img src="data:image/png;base64,'+data.image+'"/>';
                        document.querySelector('#modal_message .modal-body .text-error').innerHTML = '<p class="h5">'+message+'</p>';
                        button.click();
                        return;
                    }
                }
                return window.location = '/shop/checkout?express=1';
            });
        },
    });
});

//NON ELIMINARE é UN WORK IN PROGRESS
// odoo.define('netaddiction_theme_rewrite.limit_product_payment', function(require) {
//     "use strict";
//     var PaymentForm = require('payment.payment_form');
    
//     require('web.dom_ready');
    
//     PaymentForm.include({
//         events: _.extend({
//             "submit": "onSubmit",
//         }),
//         onSubmit: function(ev) {
//             ev.stopPropagation();
//             ev.preventDefault();

//             this._rpc({
//                 route: "/shop/cart/check_limit_order",
//             }).then(function (data) {
//                 if(data != null){
//                     var message;
//                     if(data['order_limit'] != null)
//                         message = '<span class="text-primary mb-3 d-block">Non Puoi ordinare più di '+data['order_limit']+' unità per questo prodotto:</span> '+data['product_name'];
//                     else if(data['order_limit_total'] != null)
//                         message = '<span class="text-primary mb-3 d-block">Questo prodotto non è più vendibile:</span> '+data['product_name'];
//                     else if(data.out_of_stock)
//                         message = '<span class="text-primary mb-3 d-block">Questo prodotto non è più disponibile:</span> '+data['product_name'];

//                     if (message != null){
//                         var button = document.querySelector('#error_modal');
//                         document.querySelector('#modal_message .modal-body .img-error').innerHTML = '<img src="data:image/png;base64,'+data.image+'"/>';
//                         document.querySelector('#modal_message .modal-body .text-error').innerHTML = '<p class="h5">'+message+'</p>';
//                         button.click();
//                         return;
//                     }
//                 }
                
//                 var button = $(ev.target).find('*[type="submit"]')[0]
//                 if (button.id === 'o_payment_form_pay') {
//                     return this.payEvent(ev);
//                 } else if (button.id === 'o_payment_form_add_pm') {
//                     return this.addPmEvent(ev);
//                 }
//                 return;
//             });
//         }
//     });
// });