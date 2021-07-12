odoo.define('website_all_in_one.filter', function(require) {
    "use strict";
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;
    var sAnimations = require('website.content.snippets.animation');
    var VariantMixin = require('sale.VariantMixin');
    var rpc = require('web.rpc');
    var ajax = require('web.ajax');
    var session = require('web.session');
    var Widget = require('web.Widget');
    var websale = require('website_sale.website_sale');

    sAnimations.registry.WebsiteSaleFilter = sAnimations.Class.extend(VariantMixin, {
        selector: '.oe_website_sale',
        read_events: {   
            'change form.js_filtervalue input, form.js_filtervalue select': '_onChangeFilter',
        },

        _onChangeFilter: function (ev) {
            
            if (!ev.isDefaultPrevented()) {

                ev.preventDefault();
                $(ev.currentTarget).closest("form").submit();
            }
        },
    });

    var core = require('web.core');
    var _t = core._t;
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');

    $(document).ready(function() {
        var oe_website_sale = this;

        var $giftwrap = $("#row_data");

        $('.item_image').each(function(){

            $('.raghav').removeClass('raghav');
            $("#myPack").find(".item_image").first().addClass('raghav');
            $(this).on('click',function () {
                if ( $(this).hasClass('raghav') )
                {
                    $('.raghav').removeClass('raghav');
                }
                else{
                    $('.raghav').removeClass('raghav');
                    $(this).addClass('raghav');
                }
            });
        });

        $('#giftwrapbutton').on('click', function() {
                var notes = $("#notes").val();
                var product = $(".raghav").data('id');

                ajax.jsonRpc('/shop/cart/giftwrap', 'call', {
                    'notes': notes,
                    'product':product,
                }).then(function (notes) {
                    rpc.query({
                    model: 'website',
                    method: 'get_gift_product',
                    args: [product],
                    }).then(function (data) {
                        location.reload();
                    });

                });


            });


    });

});