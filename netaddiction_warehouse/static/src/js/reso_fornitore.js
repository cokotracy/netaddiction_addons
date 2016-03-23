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
    var Pager = require('web.Pager');
    var ActionManager = require('web.ActionManager');

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
            'click .change_reverse_pick' : 'doChangeListReverse',
            'click .o_pager_next' : 'doPager',
            'click .o_pager_previous' :'doPager',
            'click .open_product' : 'doOpenProduct',
            'change #search_supplier' : 'FilterSupplier',
            'change #search' : 'SearchProduct',
            'click .reverse_select_all' : 'SelectAll',
            'click .product_selector' : 'SelectSingle',
            'click #send_reverse' : 'Reverse'
        },
        init : function(parent,supplier){
            this._super()
            this.supplier = supplier;
            this.operations = {};
            this.products = {};
            this.pager = null;
            this.limit = 40;
            this.actionmanager = new ActionManager(this);
            this.selectedProducts = {
                'scraped' : new Array(),
                'commercial' : new Array()
            };
            self = this;
            new Model('netaddiction.warehouse.operations.settings').query([]).filter([['company_id','=',session.company_id]]).all().then(function(configs){
                var ids_conf = []
                var config_conf = []
                for (var i in configs){
                    self.operations[configs[i].netaddiction_op_type]={}
                    self.operations[configs[i].netaddiction_op_type]['operation_type_id'] = configs[i].operation[0];
                    ids_conf.push(parseInt(configs[i].operation[0]));
                    config_conf.push(configs[i].netaddiction_op_type);
                }

                new Model('stock.picking.type').query(['default_location_src_id','default_location_dest_id']).filter([['id','in',ids_conf]]).all().then(function(res){
                       for (var r in res){
                            self.operations[config_conf[r]]['default_location_src_id'] = res[r].default_location_src_id
                            self.operations[config_conf[r]]['default_location_dest_id'] = res[r].default_location_dest_id
                       }

                        new Model('res.partner').query(['id','name']).filter([['supplier','=',true],['active','=',true],['parent_id','=',false]]).all().then(function(suppliers){
                           var html = ''
                           for ( var sup in suppliers){
                                var selected = ''
                                if (parseInt(suppliers[sup].id)==parseInt(self.supplier.id)){
                                    selected = ' selected="selected" ';
                                }
                                html = html + "<option value='"+suppliers[sup].id+"' "+selected+">"+suppliers[sup].name+"</option>";
                           }
                           $('#search_supplier').append(html);
                           self.get_scraped_products(self.supplier.id,1,null);
                        })
                })
                
            })
        },
        Reverse : function(e){
            var scrap = this.selectedProducts.scraped.length
            var comm =this.selectedProducts.commercial.length
            if( scrap == 0 && comm == 0){
                var not = new Notification.Warning(this)
                not.title = 'ERRORE'
                not.text = 'Devi mettere nella lista reso almeno un prodotto'
                return not.appendTo('.o_notification_manager')
            }

            new Model('stock.picking').call('create_supplier_reverse',[JSON.stringify(self.selectedProducts),self.supplier.id,JSON.stringify(self.operations)]).then(function(e){
                var not = new Notification.Warning(this)
                not.title = 'RESO EFFETTUATO'
                not.text = 'Ho creato la lista di prelievo per i prodotti selezionati'
                not.appendTo('.o_notification_manager')
            })
        },
        FilterSupplier: function(e){
            var sid = $(e.currentTarget).val();
            var name = $(e.currentTarget).find(':selected').text();
            var supplier = {
                'id' : sid,
                'name' : name
            }
            this.destroy();
            var supplier_reverse = new page_supplier_reverse(null,supplier);
            supplier_reverse.appendTo('.oe_client_action');
        },
        SearchProduct : function(e){
            var name = $(e.currentTarget).val();
            this.get_wh_products(this.supplier.id,1,name)
        },
        doChangeListReverse : function(e){
            $('.change_reverse_pick').removeClass('active_reverse');
            $(e.currentTarget).addClass('active_reverse');
            var id = $(e.currentTarget).attr('id');
          
            this.get_product_list(id);
        },
        get_product_list : function(wharehouse){
            name = null
            var searched = $('#search').val()
            if(searched!=' '){
                name=searched
            }
            if(wharehouse == 'scrapped_wh_link'){
                this.get_scraped_products(this.supplier.id,this.pager.state.current_min,name);
            }else{
                this.get_wh_products(this.supplier.id,this.pager.state.current_min,name);
            }
        },
        get_wh_products : function(supplier_id,current,product_name){
            $('#purchase_in_product_list').remove();
            $('#pager').html('');
            this.products = {};
            var location_id = this.operations.reverse_supplier.default_location_src_id[0];
            var filter = [['company_id','=',session.company_id],['location_id','=',parseInt(location_id)]]
            if (product_name != null){
                 var filter = [['company_id','=',session.company_id],['location_id','=',parseInt(location_id)],['product_id.name','ilike',product_name]]
            }
            new Model('stock.quant').query([]).filter(filter).group_by(['product_id','qty','inventory_value']).then(function(products){
                var ids = []
                var pids = {}
                for (var p in products){
                   ids.push(products[p].attributes.value[0]);
                   pids[products[p].attributes.value[0]] = {}
                   pids[products[p].attributes.value[0]]['name'] = products[p].attributes.value[1]
                   pids[products[p].attributes.value[0]]['qty'] = products[p].attributes.aggregates.qty
                   pids[products[p].attributes.value[0]]['inventory_value'] = products[p].attributes.aggregates.inventory_value
                }
                new Model('purchase.order.line').query([]).filter([['partner_id','=',parseInt(self.supplier.id)],['product_id','in',ids]]).group_by(['product_id','qty_received']).then(function(purchase){
                    var count = 0
                    var init = 0
                    var last = self.limit
                    if(parseInt(current) >1){
                        var init = current - 1
                        var last = init + self.limit
                    }
                    for ( var p in purchase){
                        if (count>=init && count<last){
                            self.products[purchase[p].attributes.value[0]] = {}
                            self.products[purchase[p].attributes.value[0]]['id'] = purchase[p].attributes.value[0]
                            self.products[purchase[p].attributes.value[0]]['qty'] = pids[purchase[p].attributes.value[0]]['qty']
                            self.products[purchase[p].attributes.value[0]]['name'] = pids[purchase[p].attributes.value[0]]['name']
                            self.products[purchase[p].attributes.value[0]]['inventory_value'] = parseFloat(pids[purchase[p].attributes.value[0]]['inventory_value']).toFixed(2)
                            self.products[purchase[p].attributes.value[0]]['qty_received'] = purchase[p].attributes.aggregates.qty_received
                        }
                        count = count + 1;
                    }
                    var pager = new Pager(self,count,current,self.limit)
                    pager.appendTo('#pager')
                    self.pager = pager
                    $('#content_reverse').html(qweb.render('table_scraped',{products : self.products}));

                    for(var i in self.selectedProducts.commercial){
                        var pid = self.selectedProducts.commercial[i].pid
                        var qta = self.selectedProducts.commercial[i].qta
                        $('#product_'+pid).closest('.product_line').find('.product_selector').prop('checked',true)
                        $('#product_'+pid).closest('.product_line').find('.qty_reverse').val(parseInt(qta))
                    }
                });
            });
        },
        get_scraped_products : function(supplier_id,current,product_name){
            $('.product_line').remove();
            $('#pager').html('');
            this.products = {};
            var location_id = this.operations.reverse_supplier_scraped.default_location_src_id[0];
            var filter = [['company_id','=',session.company_id],['location_id','=',parseInt(location_id)]]
            if (product_name != null){
                 var filter = [['company_id','=',session.company_id],['location_id','=',parseInt(location_id)],['product_id.name','ilike',product_name]]
            }
            new Model('stock.quant').query([]).filter(filter).group_by(['product_id','qty','inventory_value']).then(function(products){
                var ids = []
                var pids = {}
                for (var p in products){
                   ids.push(products[p].attributes.value[0]);
                   pids[products[p].attributes.value[0]] = {}
                   pids[products[p].attributes.value[0]]['name'] = products[p].attributes.value[1]
                   pids[products[p].attributes.value[0]]['qty'] = products[p].attributes.aggregates.qty
                   pids[products[p].attributes.value[0]]['inventory_value'] = products[p].attributes.aggregates.inventory_value
                }
                new Model('purchase.order.line').query([]).filter([['partner_id','=',parseInt(self.supplier.id)],['product_id','in',ids]]).group_by(['product_id','qty_received']).then(function(purchase){
                    var count = 0
                    var init = 0
                    var last = self.limit
                    if(parseInt(current) >1){
                        var init = current - 1
                        var last = init + self.limit
                    }
                    for ( var p in purchase){
                        if (count>=init && count<last){
                            self.products[purchase[p].attributes.value[0]] = {}
                            self.products[purchase[p].attributes.value[0]]['id'] = purchase[p].attributes.value[0]
                            self.products[purchase[p].attributes.value[0]]['qty'] = pids[purchase[p].attributes.value[0]]['qty']
                            self.products[purchase[p].attributes.value[0]]['name'] = pids[purchase[p].attributes.value[0]]['name']
                            self.products[purchase[p].attributes.value[0]]['inventory_value'] = parseFloat(pids[purchase[p].attributes.value[0]]['inventory_value']).toFixed(2)
                            self.products[purchase[p].attributes.value[0]]['qty_received'] = purchase[p].attributes.aggregates.qty_received
                        }
                        count = count + 1;
                    }
                    var pager = new Pager(self,count,current,self.limit)
                    pager.appendTo('#pager')
                    self.pager = pager
                    $('#content_reverse').html(qweb.render('table_scraped',{products : self.products}));
                    for(var i in self.selectedProducts.scraped){
                        var pid = self.selectedProducts.scraped[i].pid
                        var qta = self.selectedProducts.scraped[i].qta
                        $('#product_'+pid).closest('.product_line').find('.product_selector').prop('checked',true)
                        $('#product_'+pid).closest('.product_line').find('.qty_reverse').val(parseInt(qta))
                    }
                });
            });
        },
        doPager : function(e){
            var id = $('.active_reverse').attr('id');
            if(id=='scrapped_wh_link'){
                this.get_scraped_products(this.supplier.id,this.pager.state.current_min,null);
            }else{
                this.get_wh_products(this.supplier.id,this.pager.state.current_min,null);
            }
            
        },
        doOpenProduct : function(e){
            e.preventDefault();
            var id = $(e.currentTarget).closest('tr').attr('data-id')
            this.actionmanager.do_action({
                type: 'ir.actions.act_window',
                res_model: "product.product",
                res_id : parseInt(id),
                views: [[false, 'form']],
                target: 'new',
                context: {},
                flags: {'form': {'action_buttons': true}}
            });
        },
        SelectAll : function(e){
            var checked = $(e.currentTarget).is(':checked');
            if (checked){
                $('.product_selector').prop('checked', true);
                $('.product_selector').each(function(index,value){
                    var pid = $(value).closest('.product_line').attr('data-id')
                    var qta = $(value).closest('.product_line').find('.qty_reverse').val();
                    self.selected_product(pid,qta,'add');
                })
            }else{
                $('.product_selector').prop('checked', false);
                $('.product_selector').each(function(index,value){
                    var pid = $(value).closest('.product_line').attr('data-id')
                    var qta = $(value).closest('.product_line').find('.qty_reverse').val();
                    self.selected_product(pid,qta,'remove');
                })
            }
        },
        SelectSingle : function(e){
            var pid = $(e.currentTarget).closest('.product_line').attr('data-id');
            var qta = $(e.currentTarget).closest('.product_line').find('.qty_reverse').val();
            var checked = $(e.currentTarget).is(':checked');
            if (checked){
                this.selected_product(pid,qta,'add')
            }else{
                this.selected_product(pid,qta,'remove')
            }
        },
        selected_product : function(pid,qta,action){
            if(parseInt(qta)==0 && action=='add'){
                var name = $('#product_'+pid).text()
                var not = new Notification.Warning(this)
                not.title = 'ERRORE'
                not.text = 'La quantità del prodotto <b>'+name+'</b> non può essere 0'
                $('#product_'+pid).closest('.product_line').find('.product_selector').prop('checked', false);
                return not.appendTo('.o_notification_manager')
            }
            var id = $('.active_reverse').attr('id');
            var attr = {
                'pid' : pid,
                'qta' : qta
            }
            if(id=='scrapped_wh_link'){
                if(action=='add'){
                     this.selectedProducts.scraped.push(attr)
                 }else{
                    var i = this.selectedProducts.scraped.map(function(e) { return e.pid; }).indexOf(pid);
                    if(i != -1) {
                        this.selectedProducts.scraped.splice(i, 1);
                    }
                }
            }else{
                if(action=='add'){
                    this.selectedProducts.commercial.push(attr)
                }else{
                    var i = this.selectedProducts.commercial.map(function(e) { return e.pid; }).indexOf(pid);
                    if(i != -1) {
                        this.selectedProducts.commercial.splice(i, 1);
                    }
                }
            }
        }
    });

    core.action_registry.add("netaddiction_warehouse.supplier_reverse", reverse);
})