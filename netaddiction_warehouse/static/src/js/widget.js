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

    /*function get_products_residual(wave_id){
        new instance.web.Model('stock.picking.wave').query(['product_list']).filter([['id','=',parseInt(wave_id)]]).first().then(function(result){
            new instance.web.Model('stock.pack.operation').query(['product_id','qty_done']).filter([['id','in',result.product_list]]).all().then(function(packs){
                console.log(packs)
            })
        })
    }*/

    local.controllo_pickup = instance.Widget.extend({
    	start: function() {
    		self = this
         	return new instance.web.Model('stock.picking.wave').query(['display_name','id']).filter([['state','=','in_progress'],['in_exit','=',false],['reverse_supplier','=',false]]).all().then(function(filtered){
                
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
            "click #validateAll" : "ValidateOrderAll",
            'change .explode_barcode' : "SearchProduct",
            'click .open_under': 'OpenUnder'
        },
    	init: function(parent,wave_id,wave_name){
    		this._super(parent);
    		this.wave_id = wave_id;
    		this.wave_name = wave_name;
            this_list = this
            $('#search').val('');
            $('#search').focus();
            //get_products_residual(wave_id)
    	},
        doReturnParent : function(e){
            e.preventDefault();
            home.do_show();
            this_list.destroy();
            $('#search').val('');
            $('#search').focus();
        },
        doSearchBarcode : function(e){
            e.preventDefault();
            var barcode_list = []
            var barcode = $(e.currentTarget).val();
            barcode_list.push(barcode)

            barcode = '0'+barcode
            barcode_list.push(barcode)

            barcode = barcode.replace(/^0+/, '');
            barcode_list.push(barcode)

            barcode = barcode.toLowerCase();
            barcode_list.push(barcode)
            barcode = barcode.charAt(0).toUpperCase() + barcode.slice(1);
            barcode_list.push(barcode)

            barcode = barcode.toUpperCase();
            barcode_list.push(barcode)
            $('.open_wave_list').children().remove()
            new instance.web.Model('stock.picking').query(['id','wave_id','pack_operation_product_ids','display_name','sale_id','partner_id']).filter([
                ['pack_operation_product_ids.product_id.barcode','in',barcode_list],['wave_id','=',parseInt(this_list.wave_id)],
                ['state','not in',['draft','cancel','done']]]).all().then(function(filtered){
                    if (filtered.length == 0){
                        $('.picking_list').remove();
                        this_list.do_warn('BARCONE INESISTENTE','Il barcode  non è presente nella lista');
                        wash_and_focus_input(e.currentTarget);
                    }else{
                        var ids = [];
                        var count_products = {};
                        var count_all = {};
                        var products_array = {}
                        for (var key in filtered){
                            products_array[filtered[key].id] = {}
                            for(var i in filtered[key].pack_operation_product_ids){
                                ids.push(filtered[key].pack_operation_product_ids[i]);
                                count_products[filtered[key].id] = 0;
                                count_all[filtered[key].id] = 0;
                            }
                        }
                        new instance.web.Model('stock.pack.operation').query(['qty_done','product_id','picking_id', 'product_qty']).filter([['id','in',ids]]).all().then(function(result){
                            
                            for(var k in result){
                                var inte = parseInt(result[k].picking_id[0]);
                                count_products[inte] = count_products[inte] + parseInt(result[k].qty_done);
                                count_all[inte] = count_all[inte] + parseInt(result[k].product_qty);
                                arr = new Array()
                                arr['product_id'] = result[k].product_id
                                arr['qty'] = result[k].product_qty
                                products_array[inte][result[k].product_id[0]] = arr
                            }
                            $('.open_wave_list').append(QWeb.render('open_wave_order_list',{'orders' : filtered, 'count_products' : count_products, 'count_all' : count_all, 'explodes': products_array}))
                            $('#validateAll').show();
                        });
                    }
                });
        },
        OpenUnder: function(e){
            var wid = $(e.currentTarget).closest('tr').attr('data-id')
            $(e.currentTarget).hide();
            $('#under_tr_'+wid).show();
            $('#under_tr_'+wid).find('.explode_barcode').focus()
        },
        SearchProduct : function(e){
            var barcode_list = []
            var barcode = $(e.currentTarget).val();
            barcode_list.push(barcode)

            barcode = '0'+barcode
            barcode_list.push(barcode)

            barcode = barcode.replace(/^0+/, '');
            barcode_list.push(barcode)

            barcode = barcode.toLowerCase();
            barcode_list.push(barcode)
            barcode = barcode.charAt(0).toUpperCase() + barcode.slice(1);
            barcode_list.push(barcode)

            barcode = barcode.toUpperCase();
            barcode_list.push(barcode)
            new instance.web.Model('product.product').query(['id']).filter([['barcode','in',barcode_list]]).first().then(function(pid){
                wash_and_focus_input($('.explode_barcode'));
                var st = false
                if(pid != null){
                    var wid = $(e.currentTarget).attr('data-id');
                    $('#table_'+wid+' tr').each(function(inv,vl){
                        if(parseInt($(vl).attr('data-id')) == parseInt(pid.id) ){
                            var qty_done = parseInt($(vl).find('.qty_done').text())
                            var back_color = $(vl).css('background')
                            if(qty_done>0){
                                color_tr($('#table_'+wid+' .pid_'+pid.id));
                                
                                setTimeout(function() {
                                    return_color_tr($(vl),back_color);
                                }, 400)
                                
                                $(vl).find('.qty_done').text((qty_done-1))
                                if((qty_done-1)==0){
                                    $(vl).find('td').css('color','#dddddd');
                                    $(vl).addClass('finished')
                                }
                                st = true

                                var count_all = 0
                                var count_finished = 0
                                $('#table_'+wid+' tr').each(function(index,value){
                                    count_all = count_all +1;
                                    if($(value).hasClass('finished')){
                                        count_finished = count_finished + 1;
                                    }
                                })

                                if(count_finished==count_all){
                                    $('#complete_'+wid).show();
                                }
                            }else{
                                st = true
                                return this_list.do_warn('PRODOTTO GIA TERMINATO','Il barcode <b>'+barcode+'</b> appartiene ad un prodotto già terminato');
                            }
                        }
                    })
                }else{
                    st = true
                    return this_list.do_warn('BARCODE INESISTENTE','Il barcode <b>'+barcode+'</b> non esiste');
                }
                
                if(!st){
                    return this_list.do_warn('BARCODE NON PRESENTE','Il barcode <b>'+barcode+'</b> non è presente nell\'ordine corrente');
                }
                
            })
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
            var pop = window.open(url,'titolo','scrollbars=no,resizable=yes, width=1000,height=700,status=no,location=no,toolbar=no');
            pop.print()
            new instance.web.Model('stock.picking').call('do_validate_orders',[id]).then(function(result){
                console.log(result)
                if(result){
                    pop.close()
                    value = $(e.currentTarget).closest('tr');
                    $(value).css('color','red');
                    $(value).find('a').css('color','red');
                    $(value).find('button').hide();
                    $('#under_tr_'+id).hide()
                    $('#search').val('');
                    $('#search').focus();
                    return this_list.do_warn('ORDINE NON IN LAVORAZIONE',result['error']);
                }
                value = $(e.currentTarget).closest('tr');
                $(value).css('color','#dddddd');
                $(value).find('a').css('color','#dddddd');
                $(value).find('button').hide();
                $('#under_tr_'+id).hide()
                $('#search').val('');
                $('#search').focus();
            });
        },
        ValidateOrderAll : function(e){
            var trs = [];
            $('.nprod').each(function(index,value){
                if(parseInt($(value).text())==1){
                    trs.push(parseInt($(value).closest('tr').attr('data-id')))
                    disable_tr($(value).closest('tr'));
                    $(value).closest('tr').find('.complete').hide()
                }
            })
            new instance.web.Model('stock.picking').call('do_multi_validate_orders',[trs]).then(function(result){
                if('error' in result){
                    $('.order_tr').each(function(index,value){
                        var i = parseInt($(value).attr('data-id'))
                        $.each(result['error'], function(z,b){
                            if(parseInt(b) == i){
                                $(value).css('color','red');
                                $(value).find('a').css('color','red');
                                $(value).find('button').hide();
                            }
                        })
                        data = {
                            'ids': result['print'],
                            'model': 'stock.picking',
                        }
                        this_list.do_action({
                            type: 'ir.actions.report.xml',
                            report_name: 'netaddiction_warehouse.bolla_di_spedizione',
                            datas: data,
                            
                        })
                    })
                }else{
                    data = {
                        'ids': trs,
                        'model': 'stock.picking',
                    }
                    this_list.do_action({
                        type: 'ir.actions.report.xml',
                        report_name: 'netaddiction_warehouse.bolla_di_spedizione',
                        datas: data,
                        
                    })
                }
                
                $('#search').val('');
                $('#search').focus();
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
            var barcode_list = []
            var barcode = $(e.currentTarget).val();
            barcode_list.push(barcode)

            barcode = '0'+barcode
            barcode_list.push(barcode)

            barcode = barcode.replace(/^0+/, '');
            barcode_list.push(barcode)

            barcode = barcode.toLowerCase();
            barcode_list.push(barcode)
            barcode = barcode.charAt(0).toUpperCase() + barcode.slice(1);
            barcode_list.push(barcode)

            barcode = barcode.toUpperCase();
            barcode_list.push(barcode)
            new instance.web.Model('product.product').query(['id']).filter([['barcode','in',barcode_list]]).first().then(function(pid){
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
            var pop = window.open(url,'titolo','scrollbars=no,resizable=yes, width=1000,height=700,status=no,location=no,toolbar=no');
            pop.print()
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
                $('#search').val('');
                $('#search').focus();
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


    /**CARICO**/
    function count_products(this_cgo){
        var number_tot = 0;
        var number_prod = 0;
        for (i in this_cgo.products){
            number_prod = number_prod + 1;
            number_tot = number_tot + parseInt(this_cgo.products[i])
        }
        $('#number_tot').text(number_tot);
        $('#number_prod').text(number_prod);
    }

    function list_products(this_cgo){
        for (p in this_cgo.products){
            tr = '<tr><td class="qty_ordered">'+this_cgo.products_ordered[p]+'</td><td class="qty">'+this_cgo.products[p]+'</td><td class="pname">'+p+'</td><td class="price_'+this_cgo.pid[p]+'"></tr></tr>';
            $('#purchase_in_product_list tbody').append(tr);
        }
        get_price(this_cgo.pid)
    }

    function get_price(pids){
        ids = []
        for (p in pids){
            ids.push(parseInt(pids[p]))
        }
        price = {}
        new instance.web.Model('purchase.order.line').query(['price_unit','product_id','product_qty','order_id']).filter([['product_id','in',ids],['order_id.state','=','purchase']]).all().then(function(result){
            
            for (p in result){
                if (result[p].product_id[0] in price){
                    if(result[p].price_unit in price[result[p].product_id[0]]){
                        price[result[p].product_id[0]][result[p].price_unit] += result[p].product_qty
                    }else{
                        price[result[p].product_id[0]][result[p].price_unit] = result[p].product_qty
                    }
                }else{
                    price[result[p].product_id[0]]={}
                    price[result[p].product_id[0]][result[p].price_unit] = result[p].product_qty
                }

               
            }
           
           for ( pid in price){
                str = ''
                for (pr in price[pid]){
                    str = str + '<span title="qta '+price[pid][pr]+'">' + pr + '</span>   '
                }
                $('.price_'+pid).html(str)
           }
            
        });
    }

    local.carico = instance.Widget.extend({
        start: function() {
            this_carico = this
            new instance.web.Model('res.partner').query(['id','name']).filter([['supplier','=',true],['active','=',true],['parent_id','=',false],['company_id','=',parseInt(session.company_id)]]).all().then(function(suppliers){
                var choose = new local.carico_choose(this_carico,suppliers);
                choose.appendTo(this_carico.$el);
            })
        },
    });

    local.carico_choose = instance.Widget.extend({
        //template : 'carico_choose',
        /*events : {
            "click #gotoCarico" : "GoToCarico",
            "change #c_supplier" : "SearchWave"
        },*/
        init: function(parent,suppliers){
            this_choose = this;
            this_choose._super(parent);
            this_choose.suppliers = suppliers;
            var options ={
                    title: "Carico da Fornitore - ", 
                    subtitle: 'Scegli il Fornitore',
                    size: 'large',
                    dialogClass: '',
                    $content: instance.web.qweb.render('carico_choose2',{suppliers:suppliers}),
                    buttons: [{text: _t("Chiudi"), close: true, classes:"btn-primary"},{text:"Avanti",classes:"btn-success",click : this.GoToCarico}]
                }
            this_choose.dial = new instance.web.Dialog(this,options)
            this_choose.dial.open();

            $('#c_supplier').change(function(e){
                this_choose.SearchWave(e);
            })
        },
        GoToCarico : function(e){
            var modal_content = e.currentTarget.closest('.modal-content');
            var supplier_id = $(modal_content).find('#c_supplier').val();
            var document_number = $(modal_content).find('#document_number').val();
            wave = $(modal_content).find('#waves_supplier').val();
            
            this_choose.dial.close();
            message = '';
            if (supplier_id == ''){
                message = message + "<li><b>Fornitore</b> mancante</li>";
            }
            if (document_number == ''){
                message = message + "<li><b>Numero Documento</b> mancante</li>";
            }
            
            if(wave!=undefined){

                document_number = $('#waves_supplier option:selected').text();
                return new instance.web.Model('res.partner').query(['id','name']).filter([['id','=',parseInt(supplier_id)]]).first().then(function(sup){
                    nuovo = new local.carico_go(this_carico,supplier_id,sup.name,document_number,wave);

                    this_choose.destroy();
                    nuovo.appendTo(this_carico.$el);
                });
            }

            if(message!=''){
                return this_choose.do_warn('ERRORE',message);
            }

            return new instance.web.Model('res.partner').query(['id','name']).filter([['id','=',parseInt(supplier_id)]]).first().then(function(sup){
                return new instance.web.Model('purchase.order').query(['id','partner_id','picking_ids']).filter([['partner_id','=',parseInt(supplier_id)],['state','=','purchase']]).all().then(function(pord){
                    
                    if (pord.length==0){
                        return this_choose.do_warn("NESSUN ORDINE","Non esistono ordini di acquisto per il fornitore selezionato. Non puoi procedere oltre.");
                    }
                    
                    var ids = [];
                    for (i in pord){
                        ids.push(pord[i].picking_ids);
                    }

                    new instance.web.Model('stock.picking.wave').call('create_purchase_list',[document_number,ids]).then(function(result){
                        wave = result.id
                        nuovo = new local.carico_go(this_carico,supplier_id,sup.name,document_number,wave);
                        this_choose.destroy();
                        nuovo.appendTo(this_carico.$el);
                    })
                })
            })
            
        },
        SearchWave : function(e){
            var sup_id = $(e.currentTarget).val()
            $('.wave_row').remove();
            return new instance.web.Model('stock.picking.wave').query(['id','name']).filter([['in_exit','=',true],['state','=','in_progress'],['picking_ids.partner_id','=',parseInt(sup_id)]]).all().then(function(waves){
                if( waves.length>0){
                    html = '<tr class="oe_form_group_row wave_row"><td><b>Lista Aperta</b></td><td><select id="waves_supplier">';
                    for (i in waves){
                        html = html + '<option value="'+waves[i].id+'" selected="selected">'+waves[i].name+'</option>';
                    }
                    html = html = html + '</td></tr>';
                    $('.supplier_tr_row').after(html)
                }
            })
        }
    });

    local.carico_go = instance.Widget.extend({
        template : "carico_go",
        events : {
            "change #search" : "doBarcode",
            "click #close_wave" : "Validate"
        },
        init : function(parent,supplier_id,supplier_name,document_number,wave){
            this_cgo = this;
            this_cgo._super(parent);
            this_cgo.supplier_id = parseInt(supplier_id);
            this_cgo.document_number = document_number;
            this_cgo.wave = parseFloat(wave);
            this_cgo.supplier_name = supplier_name;
            this_cgo.products = {};
            this_cgo.products_ordered = {};
            this_cgo.pid = {}
            new instance.web.Model('stock.picking.wave').query(['id','name','picking_ids']).filter([['id','=',this_cgo.wave]]).first().then(function(result){
                
                if(result != null){
                    this_cgo.document_number = result.name
                    
                    ids = []
                    for (p in result.picking_ids){
                        ids.push(result.picking_ids[p]);
                    }
                    new instance.web.Model('stock.pack.operation').query(['id','product_id','product_qty','qty_done']).filter([['qty_done','>',0],['picking_id','in',ids]]).all().then(function(line){
                        var pqty = 0;
                        
                        for (l in line){
                            this_cgo.pid[line[l].product_id[1]] = line[l].product_id[0];
                            pqty = pqty + parseInt(line[l].product_qty)
                            if (line[l].product_id[1] in this_cgo.products){
                                this_cgo.products[line[l].product_id[1]] = parseInt(this_cgo.products[line[l].product_id[1]]) + line[l].qty_done; 
                            }else{
                                this_cgo.products[line[l].product_id[1]] = line[l].qty_done;
                            }
                            this_cgo.products_ordered[line[l].product_id[1]] = pqty
                            
                        }
                        count_products(this_cgo)
                        list_products(this_cgo)
                    })

                }
            });

       },
       doBarcode : function(e){
            var barcode = $(e.currentTarget).val();

            var barcode_list = []
            barcode_list.push(barcode)
            barcode = '0'+barcode
            barcode_list.push(barcode)
            barcode = barcode.replace(/^0+/, '');
            barcode_list.push(barcode)
            barcode = barcode.toLowerCase();
            barcode_list.push(barcode)
            barcode = barcode.charAt(0).toUpperCase() + barcode.slice(1);
            barcode_list.push(barcode)
            barcode = barcode.toUpperCase();
            barcode_list.push(barcode)

            var qta = parseInt($('#qta').val());

            $(e.currentTarget).val('').focus();
            $('#qta').val(1);

            if (qta < 0){
                return this_cgo.do_warn("QUANTITA NEGATIVA","La quantità caricata non può essere negativa");
            }
            new instance.web.Model('stock.pack.operation').query(['id','product_id','product_qty','qty_done']).filter([['picking_id.wave_id','=',this_cgo.wave],['product_id.barcode','in',barcode_list]]).all().then(function(line){
                var results = []
                var qty_residual = 0;
                var pqty = 0;
                var ids = [];
                for(i in line){
                    pqty = pqty + parseInt(line[i].product_qty)
                    if (line[i].product_qty>line[i].qty_done){
                        results.push(line[i])
                        qty_residual = qty_residual + line[i].product_qty - line[i].qty_done;
                        ids.push(line[i].id)
                    }
                }
                if (results.length==0){
                   return this_cgo.do_warn("BARCODE INESISTENTE","Il prodotto non è presente nella lista di carico o è già stato caricato");
                }

                if(qta > qty_residual){
                    return this_cgo.do_warn("QUANTITA MAGGIORE","Puoi caricari al massimo <b>"+qty_residual+"</b> pezzi del prodotto. Contatta il tuo responsabile per i rimanenti.");
                }

                new instance.web.Model('stock.pack.operation').call('complete_operation',[ids,qta])
                
                if (line[0].product_id[1] in this_cgo.products){
                    this_cgo.products[line[0].product_id[1]] = parseInt(this_cgo.products[line[0].product_id[1]]) + qta;
                }else{
                    this_cgo.products[line[0].product_id[1]] = qta
                }
                this_cgo.products_ordered[line[0].product_id[1]] = pqty
                this_cgo.pid[line[0].product_id[1]] = line[0].product_id[0];

                this_cgo.do_notify("CARICATO",qta + ' x ' + line[0].product_id[1])
                   
                $('#purchase_in_product_list tbody').html('');
                count_products(this_cgo)
                list_products(this_cgo)

            });
           
       },
       Validate : function(e){
            this_cgo.do_notify("CARICO COMPLETO",'');
            $('.oe-cp-search-view').remove();
            $('#qta').remove();
            $('#close_wave').remove();
            new instance.web.Model('stock.picking.wave').call('close_and_validate',[this_cgo.wave]);
            
       }
    });

    
    instance.web.client_actions.add(
        'netaddiction_warehouse.controllo_pickup', 'instance.netaddiction_warehouse.controllo_pickup');

    instance.web.client_actions.add(
       'netaddiction_warehouse.carico', 'instance.netaddiction_warehouse.carico');  

}

