odoo.define('netaddiction_warehouse.spara_pacchi', function (require) {
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

    var spara_pacchi = Widget.extend({
        init : function(parent){
            var rev = this
            this._super(parent)
            new Model('delivery.carrier').query(['id','name']).all().then(function(carriers){
                var options ={
                    title: "Spara Pacchi", 
                    subtitle: 'Scegli il Corriere',
                    size: 'large',
                    dialogClass: '',
                    $content: qweb.render('dialog_content_spara_pacchi',{carriers : carriers}),
                    buttons: [{text: _t("Chiudi"), close: true, classes:"btn-primary"},{text:"Avanti",classes:"btn-success",click : rev.goNext}]
                }
                    
                var dial = new Dialog(this,options)
                dial.open()
            });
        },
        goNext : function(e){
            var carrier = $('#select_carrier').val();
            var name = $('#select_carrier :selected').text();
            var carrier_selected = {
                'id' : carrier,
                'name' : name
            }
            var carrier_manifest = new Carrier_Spara_Pacchi(null,carrier_selected);
            carrier_manifest.appendTo('.oe_client_action');
            this.destroy();
        }
    });

    var Carrier_Spara_Pacchi = Widget.extend({
        template : 'carrier_spara_pacchi',
        events : {
            'change #search' : 'verifyBarcode',
        },
        init : function(parent,carrier){
            this._super()
            this.carrier = carrier;
            this.manifest = 0;
            this.buzz = new Audio("http://"+window.location.hostname+":"+window.location.port+"/netaddiction_warehouse/static/src/beep-03.mp3");
            this.more_buzz = new Audio("http://"+window.location.hostname+":"+window.location.port+"/netaddiction_warehouse/static/src/beep-05.mp3");
            this.ok_buzz = new Audio("http://"+window.location.hostname+":"+window.location.port+"/netaddiction_warehouse/static/src/beep-02.mp3");
            this.table = null; 
            var today = new Date();
            var dd = today.getDate();
            var mm = today.getMonth()+1;
            if (mm < 10 ){
                mm = '0'+mm;
            }
            if(dd<10) {
                dd='0'+dd
            }
            var yyyy = today.getFullYear();
            this.date = yyyy+'-'+mm+'-'+dd;
            var obj = this;
            var filter = [['date','=',this.date],['carrier_id.id','=',this.carrier['id']]];
            new Model('netaddiction.manifest').query().filter(filter).first().then(function(result){
                if (result == null){
                    var not = new Notification.Warning(this);
                    not.title = 'ERRORE';
                    not.text = 'OGGI NON CI SONO PACCHI';
                    return not.appendTo('.o_notification_manager');
                }
                obj.manifest = result.id;

                obj.table = new Table_Shipping(obj,result.id)
            });

            
        },
        verifyBarcode : function(e){
            var manifest = this.manifest;
            var buzz = this.buzz;
            var more_buzz = this.more_buzz;
            var ok_buzz = this.ok_buzz;
            var father = this;
            var barcode = $(e.currentTarget).val();
            var query = ['id','name','partner_id','delivery_read_manifest','delivery_barcode','manifest','origin'];
            var filter = [['delivery_barcode','=',barcode],['manifest.id','=',parseInt(manifest)]];
            
            new Model('stock.picking').query(query).filter(filter).first().then(function(picking){
                if (picking == null){
                    var not = new Notification.Warning(this);
                    not.title = 'ERRORE';
                    not.text = 'IL BARCODE NON APPARTIENE AL MANIFEST DI OGGI';
                    
                    more_buzz.play();
                    $('#search').val('').focus();
                    return not.appendTo('.o_notification_manager');
                }

                if(picking.delivery_read_manifest == true){
                    var not = new Notification.Warning(this);
                    not.title = 'PACCO GIA\' SPARATO';
                    not.text = 'HAI GIA\' SPARATO IL PACCO';
                    buzz.play();
                    $('#search').val('').focus();
                    return not.appendTo('.o_notification_manager');
                }

                new Model('stock.picking').call('confirm_reading_manifest',[picking.id]).then(function(e){
                    if (e.state == 'problem'){
                        var not = new Notification.Warning(this);
                        not.title = 'ERRORE';
                        not.text = e.message;
                        
                        more_buzz.play();
                        return not.appendTo('.o_notification_manager');
                    }else{
                        father.table.destroy();
                        father.table = new Table_Shipping(father,manifest);
                        ok_buzz.play(); 
                   }
                });

                $('#search').val('').focus();
            });
        },
        
    });

    var Table_Shipping = Widget.extend({
        template:'table',
        init : function(parent,manifest){
            this._super();
            this.picks = [];
            var obj = this;
            var query = ['id','name','partner_id','delivery_read_manifest','delivery_barcode','manifest','origin'];
            var filter = [['delivery_read_manifest','=','True'],['manifest.id','=',parseInt(manifest)]];
            new Model('stock.picking').query(query).filter(filter).all().then(function(result){
                obj.picks = result;
                obj.appendTo('#content_spara_pacchi');
            });
        }
    });

    core.action_registry.add("netaddiction_warehouse.spara_pacchi", spara_pacchi);
})