odoo.define('netaddiction_warehouse.reso_cliente', function (require) {
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

    var Reverse = Class.extend({
        init : function(parent,action){
            self = this;
            self.active_order_id = action.context.active_id;
            self.operations = {};
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
                        
                })

                new Model('netaddiction.wh.locations').query(['id']).filter([['company_id','=',session.company_id],['barcode','=','0000000002']]).first().then(function(loc){
                    self.location_reverse = loc.id;
                })

                new Model('sale.order.line').query(['product_id','product_qty','qty_delivered','qty_invoiced','qty_reverse']).filter([['order_id','=',parseInt(self.active_order_id)],['is_delivery','=',0],['is_payment','=',0]]).all().then(function(active_order_line){
                    var lines = []
                    for (var l in active_order_line){
                        if (parseInt(active_order_line[l].qty_delivered) > 0){
                            if (parseInt(active_order_line[l].qty_delivered) - parseInt(active_order_line[l].qty_reverse) > 0){
                                active_order_line[l].qty_delivered = parseInt(active_order_line[l].qty_delivered) - parseInt(active_order_line[l].qty_reverse);
                                lines.push(active_order_line[l])
                            }
                        }
                        self.active_order_line = lines;
                    }

                    new Model('sale.order').query(['picking_ids','partner_id','name']).filter([['id','=',self.active_order_id]]).first().then(function(result){
                        self.active_order = result;
                        self.open_dialog(parent);
                    });
                   
                });
            });
        },
        open_dialog : function(parent){
            var options ={
                title: "Reso", 
                subtitle: '',
                size: 'large',
                dialogClass: '',
                $content: false,
                buttons: [{text: _t("Chiudi"), close: true, classes:"btn-primary"},{text:"Avanti",classes:"btn-success",click : self.process_reverse}]
            }
                
            var dial = new Dialog(parent,options)
            dial.open()
            var reso = new content_reso(dial,self.active_order_line,self.active_order_id);
            reso.appendTo(dial.$el)
        },
        process_reverse : function(e){
            /*per un mistero che non ho capito in questo punto this è il dialog creato in open_dialog*/
            this.getChildren()[0].process_reverse();
        }
    });

    var content_reso = Widget.extend({
        template : 'content_reso',
        init: function(parent,order_line,order_id){
            this._super(parent);
            this.order_line = order_line;
            this.active_order = order_id;
        },
        process_reverse : function(){
            /*Qua invece self è reverse e this è giustamente il widget stesso*/
            var reverse_lines = {}
            var scrapped_lines = {}
            var count_scrapped= 0;
            var count_reverse = 0;
            var pids = []
            var count = 0;
            $('.reverse_line').each(function(index,element){
                if (parseInt($(element).find('.qty_reverse').val())>0 && $(element).find('.reverse_type').val()!=null){
                    count = count + 1
                    if($(element).find('.reverse_type').val()=='scrapped'){
                        scrapped_lines[$(element).attr('data-id')] = {}
                        scrapped_lines[$(element).attr('data-id')]['qta'] = $(element).find('.qty_reverse').val();
                        scrapped_lines[$(element).attr('data-id')]['type'] = $(element).find('.reverse_type').val();
                        scrapped_lines[$(element).attr('data-id')]['pid'] = $(element).attr('data-pid');
                        count_scrapped = count_scrapped + 1
                    }else{
                        reverse_lines[$(element).attr('data-id')] = {}
                        reverse_lines[$(element).attr('data-id')]['qta'] = $(element).find('.qty_reverse').val();
                        reverse_lines[$(element).attr('data-id')]['type'] = $(element).find('.reverse_type').val();
                        reverse_lines[$(element).attr('data-id')]['pid'] = $(element).attr('data-pid');
                        count_reverse = count_reverse + 1
                    }
                }   
            });

            if(count == 0){
                this.do_warn('ERRORE','Devi scegliere almeno un prodotto e un tipo di reso');
                return this.getParent().close();
            }

            if (count_scrapped>0){
                this.scrap(scrapped_lines);
            }
            if (count_reverse>0){
                this.resale(reverse_lines);
            }
        },
        scrap : function(scraped_lines){
            var oid = this.active_order;
            var move_line_ids = []
            for (var s in scraped_lines){
                var new_line = [0,0,{
                    'product_id' : parseInt(scraped_lines[s]['pid']),
                    'product_uom_qty' : parseInt(scraped_lines[s]['qta']),
                    'location_id' : parseInt(self.operations.reverse_scrape.default_location_src_id),
                    'location_dest_id' : parseInt(self.operations.reverse_scrape.default_location_dest_id),
                    'product_uom_id' : 1
                }];
                move_line_ids.push(new_line)
            }
            var attr = {
                'partner_id' : parseInt(self.active_order.partner_id[0]),
                'origin' : self.active_order.name,
                'location_dest_id' : parseInt(self.operations.reverse_scrape.default_location_dest_id),
                'picking_type_id' : parseInt(self.operations.reverse_scrape.operation_type_id),
                'location_id' : parseInt(self.operations.reverse_scrape.default_location_src_id),
                'sale_id' : parseInt(self.active_order_id),
                'move_line_ids' : move_line_ids,
            }
            new Model('stock.picking').call('create_reverse',[attr,oid]).then(function(e){

                location.reload();
            });
            this.do_notify("RESO COMPLETATO","Il reso è stato completato");
            return this.getParent().close();
        },
        resale : function(resale_lines){
            var oid = this.active_order;
            var move_line_ids = []
            for (var s in resale_lines){
                var new_line = [0,0,{
                    'product_id' : parseInt(resale_lines[s]['pid']),
                    'product_uom_qty' : parseInt(resale_lines[s]['qta']),
                    'location_id' : parseInt(self.operations.reverse_resale.default_location_src_id),
                    'location_dest_id' : parseInt(self.operations.reverse_resale.default_location_dest_id),
                    'product_uom_id' : 1
                }];
                move_line_ids.push(new_line)
                // new Model('netaddiction.wh.locations.line').call('allocate',[parseInt(resale_lines[s]['pid']),parseInt(resale_lines[s]['qta']),parseInt(self.location_reverse)]);
            }
            var attr = {
                'partner_id' : parseInt(self.active_order.partner_id[0]),
                'origin' : self.active_order.name,
                'location_dest_id' : parseInt(self.operations.reverse_resale.default_location_dest_id),
                'picking_type_id' : parseInt(self.operations.reverse_resale.operation_type_id),
                'location_id' : parseInt(self.operations.reverse_resale.default_location_src_id),
                'sale_id' : parseInt(self.active_order_id),
                'move_line_ids' : move_line_ids,
                'resale': 1
            }

            
            new Model('stock.picking').call('create_reverse',[attr,oid]).then(function(e){

                location.reload();
            });
            this.do_notify("RESO COMPLETATO","Il reso è stato completato");
            return this.getParent().close();
        }
    });

    var reso_cliente = function(parent,action){
        var reverse = new Reverse(parent,action);
    }

    
    core.action_registry.add("netaddiction_warehouse.reso_cliente", reso_cliente);

})
