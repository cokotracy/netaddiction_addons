openerp.netaddiction_groupon = function(instance, local) {
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
            }
        },
        create_pickup: function(){
            return new instance.web.Model('groupon.pickup.wave').call('create_wave').then(function(results){
                console.log(results)
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
}