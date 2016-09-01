odoo.define('netaddiction_warehouse.vatregister', function (require) {
"use strict";

    var core = require('web.core');
    var framework = require('web.framework');
    var Model = require('web.DataModel');
    var session = require('web.session');
    var web_client = require('web.web_client');
    var Widget = require('web.Widget');
    var Dialog = require('web.Dialog');
    var Notification = require('web.notification');
    var Class = require('web.Class');
    var Pager = require('web.Pager');
    var ActionManager = require('web.ActionManager');

    var _t = core._t;
    var qweb = core.qweb;

    core.qweb.add_template("/netaddiction_account/static/src/xml/vatregister.xml");
    
    var vatregister = Widget.extend({
        template : 'vatregister_top',
        events: {
                "click #search" : "get_vatregister",
                "click #products" : "filterProducts",
                'click #total': "filterTotal",
                'click #multiplayer': "filterMultiplayer"
            },
        init : function(parent){
            this._super(parent);
            this.year = []
            this.pickings = []
            var current_year = parseInt(new Date().getFullYear());
            var first_year = parseInt(2000)
            while (first_year <= current_year){
                this.year.push({'value':current_year,'name':current_year});
                current_year = current_year - 1
            }
             
            this.appendTo('.oe_client_action');
        },
        get_vatregister : function(e){
            var year = parseInt($('#year').val());
            var month = parseInt($('#month').val());
            var self = this
            new Model('stock.picking').call('get_picking_from_data',[year,month]).then(function(pickings){
                $('#content_vatregister').html('');
                self.pickings = pickings
                var vartotal = new total(null,pickings);
                return vartotal.appendTo('#content_vatregister');
            });
        },
        filterProducts : function(e){
            $('#content_vatregister').html('');
            var prod = new products(null,this.pickings);
            return prod.appendTo('#content_vatregister');
        },
        filterTotal : function(e){
            $('#content_vatregister').html('');
            var t = new total(null,this.pickings);
            return t.appendTo('#content_vatregister');
        },
        filterMultiplayer : function(e){
            $('#content_vatregister').html('');
            var t = new multiplayer(null,this.pickings);
            return t.appendTo('#content_vatregister');
        }
    });

    var multiplayer = Widget.extend({
        template:'table_vatregister_products',
        init : function(parent,pickings){
            this.pickings = {'done':{},'refund':{}}
            this.total_price = 0;
            this.price_tax = 0;
            this.edizioni = 0;
            var total_price = this.total_price;
            var price_tax = this.price_tax;
            var edizioni = this.edizioni;
            var picks = this.pickings;
            
            
            $(pickings.done).each(function(index,value){
                if(parseFloat(value.edizioni) > 0){
                    total_price = total_price + parseFloat(value.total_price);
                    price_tax = price_tax + parseFloat(value.price_tax);
                    edizioni = edizioni + parseFloat(value.edizioni);
                    if(value.pid in picks['done']){
                        picks['done'][value.pid]['qty'] = picks['done'][value.pid]['qty'] + parseInt(value.qty)
                        picks['done'][value.pid]['total_price'] = picks['done'][value.pid]['total_price'] + parseFloat(value.total_price)
                        picks['done'][value.pid]['price_tax'] = picks['done'][value.pid]['price_tax'] + parseFloat(value.price_tax)
                        picks['done'][value.pid]['edizioni'] = picks['done'][value.pid]['edizioni'] + parseFloat(value.edizioni)
                        picks['done'][value.pid]['order'].push(value.sale_id)
                    }else{
                        picks['done'][value.pid] = {
                            'qty':parseInt(value.qty),
                            'product_name':value.product_id,
                            'total_price':parseFloat(value.total_price),
                            'price_tax':parseFloat(value.price_tax),
                            'tax_id':value.tax_id,
                            'edizioni':parseFloat(value.edizioni),
                            'order':[value.sale_id]
                        }
                    }
                    picks['done'][value.pid]['order'] = $.unique(picks['done'][value.pid]['order']);
                    picks['done'][value.pid]['qty_order'] = picks['done'][value.pid]['order'].length
                }
                
            })
            this.total_price = total_price.toFixed(2);
            this.price_tax = price_tax.toFixed(2);
            this.edizioni = edizioni.toFixed(2);


            var refund_total_price = 0;
            var refund_price_tax = 0;
            var refund_edizioni = 0;
            var refund_order = [];
            $(pickings.refund).each(function(index,value){
                if(parseFloat(value.edizioni) > 0){
                    refund_order.push(value.sale_id);
                    refund_total_price = refund_total_price + parseFloat(value.total_price);
                    refund_price_tax = refund_price_tax + parseFloat(value.price_tax);
                    refund_edizioni = refund_edizioni + parseFloat(value.edizioni);
                    if(value.pid in picks['refund']){
                        picks['refund'][value.pid]['qty'] = picks['refund'][value.pid]['qty'] + parseInt(value.qty)
                        picks['refund'][value.pid]['total_price'] = picks['refund'][value.pid]['total_price'] + value.total_price
                        picks['refund'][value.pid]['price_tax'] = picks['refund'][value.pid]['price_tax'] + value.price_tax
                        picks['refund'][value.pid]['edizioni'] = picks['refund'][value.pid]['edizioni'] + value.edizioni
                        picks['refund'][value.pid]['order'].push(value.sale_id)
                    }else{
                        picks['refund'][value.pid] = {
                            'qty':parseInt(value.qty),
                            'product_name':value.product_id,
                            'total_price':parseFloat(value.total_price),
                            'price_tax':parseFloat(value.price_tax),
                            'tax_id':value.tax_id,
                            'edizioni':parseFloat(value.edizioni),
                            'order':[value.sale_id]
                        }
                    }
                    picks['refund'][value.pid]['order'] = $.unique(picks['refund'][value.pid]['order']);
                    picks['refund'][value.pid]['qty_order'] = picks['refund'][value.pid]['order'].length
                }
                
            })
            
            
            this.refund_total_price = refund_total_price.toFixed(2);
            this.refund_price_tax = refund_price_tax.toFixed(2);
            this.refund_edizioni = refund_edizioni.toFixed(2);

            this.pickings = picks;
          }
    });

    var products = Widget.extend({
        template:'table_vatregister_products',
      init : function(parent,pickings){
        this.pickings = {'done':{},'refund':{}}
        this.total_price = 0;
        this.price_tax = 0;
        this.edizioni = 0;
        var total_price = this.total_price;
        var price_tax = this.price_tax;
        var edizioni = this.edizioni;
        var picks = this.pickings;
        
        
        $(pickings.done).each(function(index,value){
            total_price = total_price + parseFloat(value.total_price);
            price_tax = price_tax + parseFloat(value.price_tax);
            edizioni = edizioni + parseFloat(value.edizioni);
            if(value.pid in picks['done']){
                picks['done'][value.pid]['qty'] = picks['done'][value.pid]['qty'] + parseInt(value.qty)
                picks['done'][value.pid]['total_price'] = picks['done'][value.pid]['total_price'] + parseFloat(value.total_price)
                picks['done'][value.pid]['price_tax'] = picks['done'][value.pid]['price_tax'] + parseFloat(value.price_tax)
                picks['done'][value.pid]['edizioni'] = picks['done'][value.pid]['edizioni'] + parseFloat(value.edizioni)
                picks['done'][value.pid]['order'].push(value.sale_id)
            }else{
                picks['done'][value.pid] = {
                    'qty':parseInt(value.qty),
                    'product_name':value.product_id,
                    'total_price':parseFloat(value.total_price),
                    'price_tax':parseFloat(value.price_tax),
                    'tax_id':value.tax_id,
                    'edizioni':parseFloat(value.edizioni),
                    'order':[value.sale_id]
                }
            }
            picks['done'][value.pid]['order'] = $.unique(picks['done'][value.pid]['order']);
            picks['done'][value.pid]['qty_order'] = picks['done'][value.pid]['order'].length
        })
        this.total_price = total_price.toFixed(2);
        this.price_tax = price_tax.toFixed(2);
        this.edizioni = edizioni.toFixed(2);


        var refund_total_price = 0;
        var refund_price_tax = 0;
        var refund_edizioni = 0;
        var refund_order = [];
        $(pickings.refund).each(function(index,value){
            refund_order.push(value.sale_id);
            refund_total_price = refund_total_price + parseFloat(value.total_price);
            refund_price_tax = refund_price_tax + parseFloat(value.price_tax);
            refund_edizioni = refund_edizioni + parseFloat(value.edizioni);
            if(value.pid in picks['refund']){
                picks['refund'][value.pid]['qty'] = picks['refund'][value.pid]['qty'] + parseInt(value.qty)
                picks['refund'][value.pid]['total_price'] = picks['refund'][value.pid]['total_price'] + value.total_price
                picks['refund'][value.pid]['price_tax'] = picks['refund'][value.pid]['price_tax'] + value.price_tax
                picks['refund'][value.pid]['edizioni'] = picks['refund'][value.pid]['edizioni'] + value.edizioni
                picks['refund'][value.pid]['order'].push(value.sale_id)
            }else{
                picks['refund'][value.pid] = {
                    'qty':parseInt(value.qty),
                    'product_name':value.product_id,
                    'total_price':parseFloat(value.total_price),
                    'price_tax':parseFloat(value.price_tax),
                    'tax_id':value.tax_id,
                    'edizioni':parseFloat(value.edizioni),
                    'order':[value.sale_id]
                }
            }
            picks['refund'][value.pid]['order'] = $.unique(picks['refund'][value.pid]['order']);
            picks['refund'][value.pid]['qty_order'] = picks['refund'][value.pid]['order'].length
        })
        
        
        this.refund_total_price = refund_total_price.toFixed(2);
        this.refund_price_tax = refund_price_tax.toFixed(2);
        this.refund_edizioni = refund_edizioni.toFixed(2);

        this.pickings = picks;
      }
    });

    var total = Widget.extend({
        template : 'table_vatregister_total',
        init : function(parent,pickings){
            this.pickings = {'done': {
                qty : 0,
                taxed: 0,
                tax:0,
                name_tax : {'Edizioni':0},
                order_qty : 0
            },'refund':{
                qty : 0,
                taxed: 0,
                tax:0,
                name_tax : {'Edizioni':0},
                order_qty : 0
            }};
            var picks = this.pickings;
            var order = [];
            $(pickings.done).each(function(index,value){
                order.push(value.sale_id)
                picks['done']['qty'] = picks['done']['qty'] + parseInt(value.qty);
                picks['done']['taxed'] = picks['done']['taxed'] + parseFloat(value.total_price);
                picks['done']['tax'] = picks['done']['tax'] + parseFloat(value.price_tax);
                picks['done']['name_tax']['Edizioni'] = picks['done']['name_tax']['Edizioni'] + parseFloat(value.edizioni);
                if (value.tax_id in picks['done']['name_tax']){
                    picks['done']['name_tax'][value.tax_id] = picks['done']['name_tax'][value.tax_id] + parseFloat(value.price_tax);
                }else{
                    picks['done']['name_tax'][value.tax_id] = parseFloat(value.price_tax);
                }

            });
            var refund_order = [];
            $(pickings.refund).each(function(index,value){
                refund_order.push(value.sale_id)
                picks['refund']['qty'] = picks['refund']['qty'] + parseInt(value.qty);
                picks['refund']['taxed'] = picks['refund']['taxed'] + parseFloat(value.total_price);
                picks['refund']['tax'] = picks['refund']['tax'] + parseFloat(value.price_tax);
                picks['refund']['name_tax']['Edizioni'] = picks['refund']['name_tax']['Edizioni'] + parseFloat(value.edizioni);
                if (value.tax_id in picks['refund']['name_tax']){
                    picks['refund']['name_tax'][value.tax_id] = picks['refund']['name_tax'][value.tax_id] + parseFloat(value.price_tax);
                }else{
                    picks['refund']['name_tax'][value.tax_id] = parseFloat(value.price_tax);
                }
            });
            refund_order = $.unique(refund_order);
            order = $.unique(order);
            picks['refund']['order_qty'] = refund_order.length
            picks['done']['order_qty'] = order.length
            this.pickings = picks;
        }
    });

    core.action_registry.add("netaddiction_warehouse.vatregister", vatregister);
})