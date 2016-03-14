odoo.define('netaddiction_warehouse.supplier_reverse', function (require) {
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

    var _t = core._t;
    var qweb = core.qweb;

    var reverse = Widget.extend({
        init : function(parent){
            var rev = this
            this._super(parent)
            new Model('res.partner').query(['id','name']).filter([['supplier','=',true],['active','=',true],['parent_id','=',false],['company_id','=',parseInt(session.company_id)]]).all().then(function(suppliers){
                var options ={
                    title: "Reso a Fornitore - ", 
                    subtitle: 'Scegli il Fornitore',
                    size: 'large',
                    dialogClass: '',
                    $content: qweb.render('dialog_content_supplier_reverse',{suppliers : suppliers}),
                    buttons: [{text: _t("Chiudi"), close: true, classes:"btn-primary"},{text:"Avanti",classes:"btn-success",click : rev.goNext}]
                }
                    
                var dial = new Dialog(this,options)
                dial.open()
            });
        },
        goNext : function(e){
            var sup_id = $('#select_supplier_reverse').val();
            var name = $('#select_supplier_reverse :selected').text();
            var supplier = {
                'id' : sup_id,
                'name' : name
            }
            var supplier_reverse = new page_supplier_reverse(null,supplier);
            supplier_reverse.appendTo('.oe_client_action');
            this.destroy();
        }
    });

    var page_supplier_reverse = Widget.extend({
        template : 'page_supplier_reverse',
        events : {
            'click .change_reverse_pick' : 'doChangeListReverse'
        },
        init : function(parent,supplier){
            this._super()
            this.supplier = supplier;
            this.get_scraped_products(this.supplier.id);
        },
        doChangeListReverse : function(e){
            $('.change_reverse_pick').removeClass('active_reverse');
            $(e.currentTarget).addClass('active_reverse');
            var id = $(e.currentTarget).attr('id');
            this.get_product_list(id);
        },
        get_product_list : function(wharehouse){
            if(wharehouse == 'scrapped_wh_link'){
                this.get_scraped_products(this.supplier.id);
            }else{
                this.get_wh_products(this.supplier.id);
            }
        },
        get_scraped_products : function(supplier_id){
            
        }
    });

    core.action_registry.add("netaddiction_warehouse.supplier_reverse", reverse);
})