openerp.netaddiction_warehouse = function(instance, local) {
	var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;
    var session = instance.session;

    var url_report = '/report/pdf/netaddiction_warehouse.bolla_di_spedizione/'

    function wash_and_focus_input(element){
        $(element).val('');
        $(element).focus();
    }

    function color_tr(tr){
        $(tr).css('background','#449d44');
        $(tr).find('a').css('color','white');
        $(tr).css('color','white');
    }

    function return_color_tr(tr,back_color){
        $(tr).css('background',back_color);
        $(tr).find('a').css('color','#337ab7');
        $(tr).css('color','#4c4c4c');
    }

    function disable_tr(tr){
        $(tr).css('color','#dddddd');
        $(tr).find('a').css('color','#dddddd');
        $(tr).addClass('finished');
    }

    function show_complete(){
        var count_finished = 0
        var count_all = 0
        $('.order_product_list').each(function(index,value){
            count_all = count_all +1;
            if($(value).hasClass('finished')){
                count_finished = count_finished + 1;
            }
        })

        if(count_finished==count_all){
            $('#validate_order').show();
        }
    }

    local.controllo_pickup = instance.Widget.extend({
    	start: function() {
    		self = this
         	return new instance.web.Model('stock.picking.wave').query(['display_name','id']).filter([['state','=','in_progress']]).all().then(function(filtered){
                var list = new local.homepage(self,filtered);
				list.appendTo(self.$el);
            });   

        },
    });

    local.openList = instance.Widget.extend({
    	template: 'open_wave',
        events: {
            "click #control_homepage" : "doReturnParent",
            "change #search" : "doSearchBarcode",
            "click .sale_order" : "doOpenOrder",
            "click .picking_order" : "doOpenPick",
            "click .partner" : "doOpenPartner",
            "click .choose" : "doGoToOrder",
            "click .complete" : "ValidateOrderTr",
            "click #validateAll" : "ValidateOrderAll"
        },
    	init: function(parent,wave_id,wave_name){
    		this._super(parent);
    		this.wave_id = wave_id;
    		this.wave_name = wave_name;
            this_list = this
            $('#search').focus();
    	},
        doReturnParent : function(e){
            e.preventDefault();
            home.do_show();
            this_list.destroy();
        },
        doSearchBarcode : function(e){
            e.preventDefault();
            var barcode = $(e.currentTarget).val();
            new instance.web.Model('stock.picking').query(['id','wave_id','pack_operation_product_ids','display_name','sale_id','partner_id']).filter([
                ['pack_operation_product_ids.product_id.barcode','=',barcode],['wave_id','=',parseInt(this_list.wave_id)],
                ['state','not in',['draft','cancel','done']]]).all().then(function(filtered){
                    if (filtered.length == 0){
                        $('.picking_list').remove();
                        this_list.do_warn('BARCONE INESISTENTE','Il barcode '+barcode.bold()+' non è presente nella lista');
                        wash_and_focus_input(e.currentTarget);
                    }else{
                        var ids = [];
                        var count_products = {};
                        for (var key in filtered){
                            for(var i in filtered[key].pack_operation_product_ids){
                                ids.push(filtered[key].pack_operation_product_ids[i]);
                                count_products[filtered[key].id] = 0;
                            }
                        }
                        new instance.web.Model('stock.pack.operation').query(['qty_done','product_id','picking_id']).filter([['id','in',ids]]).all().then(function(result){
                            for(var k in result){
                                var inte = parseInt(result[k].picking_id[0]);
                                count_products[inte] = count_products[inte] + parseInt(result[k].qty_done);
                            }
                            $('.open_wave_list').append(QWeb.render('open_wave_order_list',{'orders' : filtered, 'count_products' : count_products}))
                            $('#validateAll').show();
                        });
                    }
                });
        },
        doOpenOrder : function(e){
            e.preventDefault();
            var id = $(e.currentTarget).attr('data-id');
            this_list.do_action({
                type: 'ir.actions.act_window',
                res_model: "sale.order",
                res_id : parseInt(id),
                views: [[false, 'form']],
                target: 'new',
                context: {},
            });
        },
        doOpenPick : function(e){
            e.preventDefault();
            var id = $(e.currentTarget).attr('data-id');
            this_list.do_action({
                type: 'ir.actions.act_window',
                res_model: "stock.picking",
                res_id : parseInt(id),
                views: [[false, 'form']],
                target: 'new',
                context: {},
            });
        },
        doOpenPartner : function(e){
            e.preventDefault();
            var id = $(e.currentTarget).attr('data-id');
            this_list.do_action({
                type: 'ir.actions.act_window',
                res_model: "res.partner",
                res_id : parseInt(id),
                views: [[false, 'form']],
                target: 'new',
                context: {},
            });
        },
        doGoToOrder : function(e){
            e.preventDefault();
            var id = $(e.currentTarget).closest('tr').attr('data-id');
            var picking_order = $(e.currentTarget).closest('tr').find('.picking_order').text();
            var sale_order = $(e.currentTarget).closest('tr').find('.sale_order').text();
            var order_name = sale_order + ' | ' + picking_order;
            new instance.web.Model('stock.pack.operation').query(['qty_done','product_id','picking_id']).filter([['picking_id','=',parseInt(id)]]).all().then(function(result){
                var new_order = new local.singleOrder(this_list,id,this_list.wave_name,order_name,result);
                this_list.do_hide();
                new_order.appendTo(home.parent.$el);
            })
            
        },
        ValidateOrderTr : function(e) {
            var id = $(e.currentTarget).closest('tr').attr('data-id');
            url = url_report+id
            window.open(url,'titolo','scrollbars=no,resizable=yes, width=1000,height=700,status=no,location=no,toolbar=no');
            new instance.web.Model('stock.picking').call('do_validate_orders',[id]).then(function(result){
                value = $(e.currentTarget).closest('tr');
                $(value).css('color','#dddddd');
                $(value).find('a').css('color','#dddddd');
                $(value).find('button').hide();
            });
        },
        ValidateOrderAll : function(e){
            var trs = [];
            $('.nprod').each(function(index,value){
                if(parseInt($(value).text())==1){
                    trs.push(parseInt($(value).closest('tr').attr('data-id')))
                }
            })
            data = {
                'ids': trs,
                'model': 'stock.picking',
            }
            this_list.do_action({
                'type': 'ir.actions.report.xml',
                'report_name': 'netaddiction_warehouse.bolla_di_spedizione',
                'datas': data,
            })
        }
    });

    local.singleOrder = instance.Widget.extend({
        template : 'single_order',
        events : {
            "click #control_wave" : "returnWave",
            "click #control_homepage" : "returnHome",
            "click .product" : "GoToProduct",
            "change #search_in_order" : "SearchProduct",
            "click #gotoSped" : "GoToPicking",
            "click #validate_order" : "ValidateOrder",
            
        },
        init : function(parent,id,wave_name,order_name,products){
            this._super(parent);
            this.order_id = id;
            this.wave_name = wave_name;
            this.order_name = order_name;
            this.products = products;
            this_order = this;
        },
        returnWave : function(e){
            e.preventDefault();
            this_list.do_show();
            this_order.destroy();
        },
        returnHome : function(e){
            e.preventDefault();
            home.do_show();
            this_list.destroy();
            this_order.destroy();
        },
        GoToProduct : function(e){
            e.preventDefault();
            var id = $(e.currentTarget).attr('data-id');
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "product.product",
                res_id : parseInt(id),
                views: [[false, 'form']],
                target: 'new',
                context: {},
            });
        },
        GoToPicking : function(e){
            e.preventDefault();
            var id = $(e.currentTarget).attr('data-id');
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "stock.picking",
                res_id : parseInt(id),
                views: [[false, 'form']],
                target: 'new',
                context: {},
            });
        },
        SearchProduct : function(e){
            var barcode = $(e.currentTarget).val();
            new instance.web.Model('product.product').query(['id']).filter([['barcode','=',barcode]]).first().then(function(pid){
                if(pid != null){
                    for(var p in this_order.products){
                        if(this_order.products[p].product_id[0] == pid.id){
                            var qty_done = parseInt($('.pid_'+pid.id).find('.qty_done').text());
                            if(qty_done>0){
                                var back_color = $('.pid_'+pid.id).css('background');
                                color_tr($('.pid_'+pid.id));
                                return setTimeout(function() {
                                    return_color_tr($('.pid_'+pid.id),back_color);
                                    wash_and_focus_input($('#search_in_order'));
                                    $('.pid_'+pid.id).find('.qty_done').text((qty_done-1));
                                    if((qty_done-1)==0){
                                        disable_tr($('.pid_'+pid.id));
                                    }

                                    show_complete();

                                }, 1100);
                            }else{
                                return this_order.do_warn('PRODOTTO GIA TERMINATO','Il barcode <b>'+barcode+'</b> appartiene ad un prodotto già terminato');
                            }
                        }
                    }
                }else{
                    return this_order.do_warn('BARCODE INESISTENTE','Il barcode <b>'+barcode+'</b> non esiste');
                }
                
                return this_order.do_warn('BARCODE NON PRESENTE','Il barcode <b>'+barcode+'</b> non è presente nell\'ordine corrente');
            })
        },
        ValidateOrder : function(e){
            url = url_report+this_order.order_id
            window.open(url,'titolo','scrollbars=no,resizable=yes, width=1000,height=700,status=no,location=no,toolbar=no');
            new instance.web.Model('stock.picking').call('do_validate_orders',[this_order.order_id]).then(function(result){
                $('.order_tr').each(function(index,value){
                    if($(value).attr('data-id')==this_order.order_id){
                        $(value).css('color','#dddddd');
                        $(value).find('a').css('color','#dddddd');
                        $(value).find('button').hide();
                        this_order.destroy();
                        this_list.do_show();
                    }
                })
            });
        },
        
    });


    local.homepage = instance.Widget.extend({
    	template: 'control_pick_up_homepage',
    	events: {
    		"click .wave_tr" : "doOpenWave",
            },
    	init: function(parent,waves){
    		this._super(parent);
            this.waves = waves;
            this.parent = parent;
            home = this;
    	},
    	doOpenWave : function(e){
    		var id = $(e.currentTarget).attr('data-id');
    		var wave_name = $(e.currentTarget).find('.wave_name').text();
    		var open = new local.openList(home,id,wave_name);
            home.do_hide();
            open.appendTo(home.parent.$el)
    	}
    });


    instance.web.client_actions.add(
        'netaddiction_warehouse.controllo_pickup', 'instance.netaddiction_warehouse.controllo_pickup');
}