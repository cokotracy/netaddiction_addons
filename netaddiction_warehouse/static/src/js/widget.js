odoo.define('netaddiction_warehouse.controllo_pickup', function (require) {
"use_strict"

        var Widget = require('web.Widget');   
        var core = require('web.core'); 
        var Model = require('web.Model');  
        var Notification = require('web.notification');
        var Action = require('web.ActionManager');
        var _t = core._t;

        var Wave = new Model('stock.picking.wave');  
        var Pick = new Model('stock.picking');
        var Orders = new Model('sale.order');
        var Pick_line = new Model('stock.pack.operation');
        var Product = new Model('product.product');


        HomePage = Widget.extend({
            start: function() {
                this.alive(Wave.query(['display_name','id']).filter([['state','=','in_progress']]).all()).then(function(filtered){
                	var waves = new Waves(this,filtered);
                	waves.appendTo('.oe_client_action');
                });
                
            },
        });

        Cp_form = Widget.extend({
            template : "control_pick_up_form",
            init : function(parent){
                this._super(parent)
            }
        });

        Pick_list = Widget.extend({
            template : "stock_picking_list",
            init: function(parent,pickings){
                this._super(parent);
                this.pickings = pickings;
            }
        });

        Waves = Widget.extend({
        	template: "wave_lists",
            events: {
                "click .cp_wave_link": "doActionClickWave",
                "change #cp_barcode" : "doActionChangeBarcode",
                "click .action_orders" : "doOpenOrder",
                "click .action_pickings" : "doOpenPicking",
                "click #order_barcode" : "changeBorder",
                "change #order_barcode" : "doActionControlProduct",
                "click #validate_order" : "doActionValidateOrder",
            },
            init: function(parent,waves) {
            	this._super(parent);
            	this.waves = waves;
            },
            doActionClickWave: function(e) {
                e.preventDefault();
                if(this.$(e.currentTarget).find('.modify').length>0){
                    this.$(e.currentTarget).find('.cp_block_title').removeClass('cp_block_title modify').addClass('cp_block_content');
                    this.$('.form_control').remove();
                }else{
                    this.$el.find('.cp_block_title').removeClass('cp_block_title modify').addClass('cp_block_content');
                    this.$('.form_control').remove();
                    this.$(e.currentTarget).find('.cp_block_content').removeClass('cp_block_content').addClass('cp_block_title modify');
                    var cp_form = new Cp_form();
                    cp_form.insertAfter(this.$(e.currentTarget));
                }
                
            },
            doActionChangeBarcode: function(e){
                var barcode = this.$(e.currentTarget).val();
                var wave_id = this.$(e.currentTarget).parent().parent().attr('data-wave_id');
                this.alive(Pick.query(['id','wave_id','pack_operation_product_ids','display_name','origin']).filter([
                ['pack_operation_product_ids.product_id.barcode','=',barcode],['wave_id','=',parseInt(wave_id)],
                ['state','not in',['draft','cancel','done']]]).all()).then(function(filtered){
                    
                    if (filtered.length == 0){
                        $('.picking_list').remove();
                        var notify = new Notification.Warning(this,'ERRORE','Il barcode '+barcode.bold()+' non è presente nella wave')
                        notify.appendTo('.o_notification_manager');$(e.currentTarget).focus();
                        $(e.currentTarget).val('');
                    }else{
                        $('.picking_list').remove();
                        $(e.currentTarget).focus();
                        $(e.currentTarget).val('');
                        var pick = new Pick_list(this,filtered);
                        pick.insertAfter('#cp_barcode');
                        var ids = [];
                        var count_lines = [];
                        for (var key in filtered){
                            for(var i in filtered[key].pack_operation_product_ids){
                                ids.push(filtered[key].pack_operation_product_ids[i]);
                                count_lines[filtered[key].id] = 0;
                            }
                        }
                        
                        Pick_line.query(['qty_done','product_id','picking_id']).filter([['id','in',ids]]).all().then(function(result){
                                for (var key in result){
                                    html = '<div class="'+result[key].product_id[0]+' count_lines">'+'<b>'+result[key].qty_done+'</b> X ';
                                    html = html +result[key].product_id[1]+'</div>';
                                    $('.line_picks_'+result[key].picking_id[0]).append(html);
                                    var inte = parseInt(result[key].picking_id[0]);
                                    count_lines[inte] = count_lines[inte] + parseInt(result[key].qty_done);
                                }
                                for (p in count_lines){
                                    if (count_lines[p] == 1){
                                        $('.line_picks_'+p).parent().parent().css('border-color','black')
                                        $('.line_picks_'+p).parent().parent().find('.cp_block_title').append('<button id="validate_order">VALIDA</button>');
                                        
                                        $('.line_picks_'+p).parent().remove()
                                    }
                                }
                        });
                        
                        
                    }
                });
            },
            doOpenOrder : function(e){
                var act = new Action();
                var ord_name = $(e.currentTarget).text();
                Orders.query(['id']).filter([['name','=',ord_name]]).first().then(function(orders){
                    var id = orders.id
                    act.do_action({
                        type: 'ir.actions.act_window',
                        res_model: "sale.order",
                        res_id : id,
                        views: [[false, 'form']],
                        target: 'new',
                        context: {},
                        flags: {'form': {'action_buttons': true}}
                    });
                });
            },
            doOpenPicking : function(e){
                var act = new Action();
                var pick_name = $(e.currentTarget).text();
                Pick.query(['id']).filter([['name','=',pick_name]]).first().then(function(picks){
                    var id = picks.id
                    act.do_action({
                        type: 'ir.actions.act_window',
                        res_model: "stock.picking",
                        res_id : id,
                        views: [[false, 'form']],
                        target: 'new',
                        context: {},
                        flags: {'form': {'action_buttons': true}}
                    });
                });
            },
            changeBorder : function(e){
                $(e.currentTarget).parent().parent().css('border-color','black');
            },
            doActionControlProduct : function(e){
                var barcode = $(e.currentTarget).val();
                Product.query(['id']).filter([['barcode','=',barcode]]).first().then(function(result){
                    if(!result){
                        var notify = new Notification.Warning(this,'ERRORE','Il barcode '+barcode.bold()+' non è presente nell\'ordine ')
                        notify.appendTo('.o_notification_manager');
                        $(e.currentTarget).focus();
                        $(e.currentTarget).val('');
                    }else{
                        $(e.currentTarget).parent().find('.'+result.id).css('background-color','#87D37C');
                        setTimeout(function() {
                            $(e.currentTarget).parent().find('.'+result.id).css('background-color','white');
                        }, 1100);
                        var qty = $(e.currentTarget).parent().find('.'+result.id).find('b').text();
                        if (parseInt(qty)==1){
                            $(e.currentTarget).parent().find('.'+result.id).slideUp(1000);
                            setTimeout(function() {
                                $(e.currentTarget).parent().find('.'+result.id).remove();
                            }, 1000);
                        }else{
                            $(e.currentTarget).parent().find('.'+result.id).find('b').text(parseInt(qty)-1);
                        }
                        
                        $(e.currentTarget).focus();
                        $(e.currentTarget).val('');
                       
                        setTimeout(function(){
                            var count = $(e.currentTarget).parent().find('.count_lines').length;
                            if(count == 0){
                                setTimeout(function() {
                                    $(e.currentTarget).parent().parent().find('.cp_block_title').append('<button id="validate_order">VALIDA</button>');
                                    $(e.currentTarget).parent().remove();
                                }, 1000);
                                
                            }
                        },1100);
                    }
                })
            },
            doActionValidateOrder : function(e){
                var pick_name = $(e.currentTarget).parent().find('.action_pickings').text();
                act = new Action()
                
                Pick.query(['id']).filter([['name','=',pick_name]]).first().then(function(picks){
                    var id = picks.id
                    /*Decidiamo se mettere ordine o delivery o altro report*/
                    url = '/report/html/netaddiction_warehouse.bolla_di_spedizione/'+id
                    window.open(url,'titolo','scrollbars=no,resizable=yes, width=1000,height=700,status=no,location=no,toolbar=no');
                    Pick.call('do_validate_orders',[id]).then(function(result){
                        $(e.currentTarget).parent().parent().slideUp(1000);
                            setTimeout(function(){
                                $(e.currentTarget).parent().parent().remove();
                            }, 1000);
                    });
                    /*act.do_action({
                        name : 'Bolla di spedizione',
                        type: 'ir.actions.report.xml',
                        report_name: "stock.report_deliveryslip",
                        file : "stock.report_deliveryslip",
                        datas : {
                         'ids': [id],
                         'model': 'stock.picking'
                             }
                    });*/

                });
                
            },
        });


        core.action_registry.add(
            'netaddiction_warehouse.controllo_pickup.homepage', HomePage);
});