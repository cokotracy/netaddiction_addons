openerp.netaddiction_groupon = function(instance, local) {
    var QWeb = instance.web.qweb;

    instance.web.ListView.include({
        render_buttons: function() {
            var self = this;
            this._super.apply(this, arguments)
            if (self.$buttons) {
                if(self.model == 'netaddiction.groupon.sale.order'){
                    self.$buttons.find('.o_list_button_import').remove();
                    self.$buttons.append('<button  class="btn btn-sm btn-info oe_button_import_groupon" type="button">Importa Ordini</button> ')
                    self.$buttons.append('<button  class="btn btn-sm btn-warning oe_button_create_list_pickup" type="button">Crea Lista</button>')
                    self.$buttons.find('.oe_button_create_list_pickup').on('click', self.proxy('create_pickup'));
                    self.$buttons.find('.oe_button_import_groupon').on('click', self.proxy('import_groupon'));
                }
                if(self.model == 'groupon.reserve.product' || self.model == 'groupon.return.product' || self.model == 'groupon.pickup.wave'){
                    self.$buttons.find('.o_list_button_import').remove();
                }
            }
        },
        create_pickup: function(){
            var self = this;
            return new instance.web.Model('groupon.pickup.wave').call('create_wave').then(function(results){
                if(results == 'ok'){
                    self.do_notify('Lista creata con successo');
                }else{
                    self.do_warn('Errore creazione lista', results)
                }
            });
        },
        import_groupon: function(){
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "netaddiction.groupon.register",
                views: [[false, 'form']],
                target: 'new',
                context: {},
                flags: {'form': {'action_buttons': false }}
            });
        }
    });

    instance.web.FormView.include({
        render_buttons: function() {
            var self = this;
            this._super.apply(this, arguments)
            if(self.model == "groupon.pickup.wave"){
                self.$buttons.find('.oe_form_button_create').remove();
                self.$buttons.find('.oe_form_button_edit').css('float','left');
                $('.oe-cp-buttons').css('width','50%');
                
                self.$buttons.append(' <button  class="btn btn-sm btn-info oe_button_print_groupon" type="button" style="margin-left:5px">Stampa Etichette</button> ');
                self.$buttons.find('.oe_button_print_groupon').on('click', self.proxy('print_groupon'));
            }
        },
        print_groupon: function(){
            var self = this;
            var id = self.dataset.ids[self.dataset.index];
            $('.oe-control-panel').hide();
            $('.oe_view_manager_current').hide();
            var html = '';
            new instance.web.Model('groupon.pickup.wave').call('get_picks',[id]).then(function(results){
                console.log(results)
                $.each(results,function(index,value){
                    html = html + '<div class="page">';
                    html = html + '<table  border="0" cellspacing="0" cellpadding="0" style="font-family:Arial, Helvetica, sans-serif; font-size:12px; font-weight:bold; line-height:14px; margin:0px; padding:0px; ">';
                    html = html + '<tr><td><center><em style="font-size:12px">Ordine:</em>'+value.groupon_id+'<br/><em style="font-size:12px">Dest:</em>'+value.name+'</center></td>';

                    html = html + '</tr><tr><td><image src="'+value.pick_barcode+'"/><br/><center><span>`+value.barcode+`</span></center></td></tr></table>';
                            
                    html = html +  '</div>';
                    html = html +  '<br/><br/><br/>';
                });
                    

                $('.oe_application').append(html)
            });
            //$('.oe_application').append(id)
        }
    });
}