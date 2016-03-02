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
                for (var i in configs){
                    self.operations[configs[i].netaddiction_op_type]={}
                    self.operations[configs[i].netaddiction_op_type]['operation_type_id'] = configs[i].operation[0];
                    new Model('stock.picking.type').query(['default_location_src_id','default_location_dest_id']).filter([['id','=',configs[i].operation[0]]]).first().then(function(res){
                        self.operations[configs[i].netaddiction_op_type]['default_location_src_id'] = res.default_location_src_id[0];
                        self.operations[configs[i].netaddiction_op_type]['default_location_dest_id'] = res.default_location_dest_id[0];
                    })
                }
                new Model('sale.order.line').query(['product_id','product_qty','qty_delivered','qty_invoiced']).filter([['order_id','=',parseInt(self.active_order_id)]]).all().then(function(active_order_line){
                    self.active_order_line = active_order_line;

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
            var reso = new content_reso(dial,self.active_order_line);
            reso.appendTo(dial.$el)
        },
        process_reverse : function(e){
            /*per un mistero che non ho capito in questo punto this è il dialog creato in open_dialog*/
            this.getChildren()[0].process_reverse();
        }
    });

    var content_reso = Widget.extend({
        template : 'content_reso',
        init: function(parent,order_line){
            this._super(parent);
            this.order_line = order_line;
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
        },
        scrap : function(scraped_lines){
            var pack_operation_product_ids = []
            for (var s in scraped_lines){
                var new_line = [0,0,{
                    'product_id' : parseInt(scraped_lines[s]['pid']),
                    'product_qty' : parseInt(scraped_lines[s]['qta']),
                    'location_id' : parseInt(self.operations.reverse_scrape.default_location_src_id),
                    'location_dest_id' : parseInt(self.operations.reverse_scrape.default_location_dest_id),
                    'product_uom_id' : 1
                }];
                pack_operation_product_ids.push(new_line)
            }
            var attr = {
                'partner_id' : parseInt(self.active_order.partner_id[0]),
                'origin' : self.active_order.name,
                'location_dest_id' : parseInt(self.operations.reverse_scrape.default_location_dest_id),
                'picking_type_id' : parseInt(self.operations.reverse_scrape.operation_type_id),
                'location_id' : parseInt(self.operations.reverse_scrape.default_location_src_id),
                'sale_id' : parseInt(self.active_order_id),
                'pack_operation_product_ids' : pack_operation_product_ids,
            }
            new Model('stock.picking').call('create_reverse',[attr]);
            this.do_notify("RESO COMPLETATO","Il reso è stato completato");
            return this.getParent().close();
        }
    });

    var reso_cliente = function(parent,action){
        var reverse = new Reverse(parent,action);
    }

    
    core.action_registry.add("netaddiction_warehouse.reso_cliente", reso_cliente);

})
