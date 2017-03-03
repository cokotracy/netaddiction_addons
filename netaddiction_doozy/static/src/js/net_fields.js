odoo.define('netaddiction_doozy',function(require){
    var ControlPanel = require('web.ControlPanel');
    var core = require('web.core');
    var data = require('web.data');
    var Dialog = require('web.Dialog');
    var common = require('web.form_common');
    var FormView = require('web.FormView');
    var ListView = require('web.ListView');
    var Model = require('web.DataModel');
    var session = require('web.session');
    var utils = require('web.utils');
    var ViewManager = require('web.ViewManager');
    var formats = require('web.formats');

    var _t = core._t;
    var QWeb = core.qweb;
    var COMMANDS = common.commands;
    var list_widget_registry = core.list_widget_registry;

    /**
    Può sostituire il widget per i field: many2many, one2many
    Configurazione nel template:
    es: <field name="item_ids" widget="net_2many" net_fields="product_id,qty_available_now,typology,qty_lmit_b2b,purchase_price,percent_price,b2b_real_price" 
        searchable="product_id.id,product_id.barcode,product_id.name" notaddlist="1"/>
    Param:
        widget: impostare a "net_2many"
        net_fields: i fields da visualizzare separati da virgole
        searchable: se si vuole far ricercare le righe inserire i fields di su cui ricercare 
                    (nel caso di proprietà di altri field usare il punto es: product_id.barcode cerca nei barcode dei dei prodotti di quella riga)
        notaddlist: se impostato a 1 impedisce l'aggiunta da lista, ossia da righe già esistenti, ma permette solo la creazione di una nuova riga
        domain: filtra la scelta da lista secondo il dominio specificato 
        context: serve nell'aggiunta del nuovo record per settare alcuni paramentri di default (es:company_id o altre cose) ad un valore deciso prima
        delete: se impostato (qualsiasi valore) cancella la riga corrispondente dal db, se quell'oggetto ha un collegamento ad una altro oggetto ritorna
                un errore e non toglie il valore dal field
        inline: se impostato (qualsiasi valore) la modifica della riga avviene inline (ad ogni onchange scrive nel db quel nuovo campo)
    **/

    /**continuare con add, delete con il trigger del save e dell'annullamento
    **/
    var Net2Many = common.AbstractField.extend({
        events: {
            'click .open_object': 'OpenObj',
            'click .next_page': 'NextPage',
            'click .prev_page': 'PrevPage',
            'click .net_button_search': 'Search',
            'click .net_row': 'OpenRowObj',
            'click .net_add_button': 'New_Row',
            'click .net_many_delete': 'Delete_Row',
            'click .net_add_new_row': 'New_Obj_Row',
            'change .input_modify': 'ModifyInput',
            'click .many2one_input_modify': "ClickMany2One",
            'change .many2one_input_modify': "Autocomplete",
            'click .autocomplete_go_product': "OpenObj",
            'click .autocomplete_results': "ModifyMany2One",
            'click .autocomplete_next': 'AutocompleteNext',
            'click .autocomplete_prev': 'AutocompletePrev'
        },
        init: function(field_manager, node) {
            this._super(field_manager, node);
            this.set({'value': false});
        },
        start: function(){
            var self = this;
            var relation = self.field.relation;
            /**setta i nuovi parametri di default**/
            if(self.node.attrs.hasOwnProperty("net_fields")){
                /**splitta in un array i fields che devono essere messi in vista**/
                if(!Array.isArray(self.node.attrs.net_fields) && self.node.attrs.net_fields){
                    self.node.attrs.net_fields = self.node.attrs.net_fields.split(',');
                }
            }
            if(!self.node.attrs.hasOwnProperty("net_fields")){
                /**se non ha il parametro net_fields allora lo setta a ID**/
                self.node.attrs.net_fields = ['id'];
            }

            if(self.node.attrs.hasOwnProperty("searchable")){
                /**splitta in un array i fields in cui si deve ricercare**/
                if(!Array.isArray(self.node.attrs.searchable) && self.node.attrs.searchable){
                    self.node.attrs.searchable = self.node.attrs.searchable.split(',');
                }
                /**parametro di ricerca, ci vanno gli id trovati**/
                self.node.attrs.searchable_ids = false;
            }
            if(!self.node.attrs.hasOwnProperty("searchable")){
                /**se non c'è searchable allora non ricerco nulla**/
                self.node.attrs.searchable = false;
                self.node.attrs.searchable_ids = false;
            }

            new Model(relation).call('fields_get',[]).then(function(fields){
                if(self.node.attrs.hasOwnProperty("searchable")){
                    self.construct_searchable_filter(self.node.attrs.searchable, fields);
                }
                self.construct_net_fields(fields);
            });

            self.node.pager = {};
            self.deleted_row = [];
            
            /**inizializzo la vista**/
            self.set_paginator(0,20,self.get('value').length);
            self.render_value(self.node.pager.ids);

            /**trigger sul cambio di valore - esempio cambio oggetto etc**/
            this.on("changed_value", this, function() {
                if(self.getParent().datarecord.hasOwnProperty('id')){
                    $(self.$el).find('tbody').remove();
                    self.set_paginator(0,20,self.get('value').length);
                    self.render_value(self.node.pager.ids);
                }else{
                    /**per il crea nuovo**/
                    var values = self.get('value');
                    $.each(values,function(i,v){
                        if(typeof(v)=='object'){
                            values = [];
                        }
                    });
                    if(values.length>0){
                        self.set_paginator(0, self.get_pager_value('limit'), values.length);
                        self.render_value(values);
                    }else{
                        self.set_paginator(0, 0, 0);
                        self.$el.html(QWeb.render("Net2Many", {widget: self}));
                    }
                }
            });

            /*trigger sul readonly*/
            this.on("change:effective_readonly", this, function() {
                if(self.getParent().datarecord.hasOwnProperty('id')){
                    self.$el.html(QWeb.render("Net2Many", {widget: self, results:self.now_results}));
                }
            });
            /**trigger sul salvataggio del form**/
            var model = self.getParent().model;
            var parent_id = self.getParent().datarecord.id;
            this.getParent().on('save',this, function(e){
                var attr = {};
                if(Number.isInteger(e)){
                    if(self.node.attrs.hasOwnProperty("delete")){
                        var m = self.field.relation;
                        new Model(m).call('unlink',[self.deleted_row]);
                    }
                }else{
                    var values = self.get_value();
                    attr[self.name] = values;
                    new Model(model).call('write',[parseInt(parent_id),attr]);
                    self.set_paginator(0, self.get_pager_value('limit'), self.get('value').length);
                    self.render_value(self.node.pager.ids);
                    if(self.node.attrs.hasOwnProperty("delete")){
                        var m = self.field.relation;
                        new Model(m).call('unlink',[self.deleted_row]);
                    }
                }
            })
        },
        get_value: function(){
            var self = this;
            var is_n2many = false;
            if(this.field.type == "one2many"){
                is_n2many = true;
            }
            if(this.field.type == "many2many"){
                is_n2many = true;
            }
            if(is_n2many){
                var res = this.get('value');
                $.each(res,function(i,v){
                    if(typeof(v)=='object'){
                        self.internal_set_value(false);
                        res = false
                    }
                });
                if(res){
                    var results = [[6,false,res]];
                    return results
                }else{
                    return false;
                }
                
            }else{
                return this.get('value');
            }
        },
        render_value: function(ids){
            var self=this;
            /**estrae e renderizza i valori**/
            var fields = self.node.attrs.net_fields;
            var relation = self.field.relation;

            if(!ids){
                self.set_paginator(0, 0, 0);
                self.$el.html(QWeb.render("Net2Many", {widget: self}));
            }else{
                new Model(relation).query(fields).filter([['id', 'in',ids]]).all().then(function(results){
                    var objs = [];
                    $.each(results,function(i,result){
                        $.each(fields, function(x,field){
                            if(self.node.attrs.net_fields_property[field].type=='float'){
                                result[field] = result[field].toLocaleString();
                            }
                            if(self.node.attrs.net_fields_property[field].type=='selection'){
                                $.each(self.node.attrs.net_fields_property[field].selection, function(d,sel){
                                    if(sel[0]==result[field]){
                                        result[field] = sel[1];
                                    }
                                });
                            }
                        })
                    });
                    self.now_results = results;
                    self.$el.html(QWeb.render("Net2Many", {widget: self, results:results}));
                });
            }
        },
        New_Row: function(){
            var self = this;
            
            var options ={
                title: "Nuovo " + self.string, 
                subtitle: '',
                size: 'large',
                dialogClass: '',
                buttons: [{text: _t("Chiudi"), close: true, classes:"btn-primary"}]
            }
                
            var dial = new Dialog(this,options);
            dial.open();
            self.get_all_relation_objects(0,20,dial,false);
        },
        New_Obj_Row: function(){
            var self=this;
            var context = self.build_context().eval();
            var object = self.field.relation;
            var pop = new common.FormViewDialog(this, {
                res_model: object,
                res_id:false,
                context: context,
                title: _t("Open: ") + self.string,
                readonly:this.get("effective_readonly")
            }).open();
            pop.on('record_saved', self, function(){
                var new_ids = pop.dataset.ids;
                var old_ids = self.get('value');
                if(!old_ids){
                    old_ids=[];
                }
                $.each(new_ids,function(i,v){
                    old_ids.unshift(parseInt(v));
                });
                self.internal_set_value(old_ids);
                if(!self.getParent().datarecord.hasOwnProperty('id')){
                    self.set_paginator(0,20,old_ids.length);
                }else{
                    self.set_paginator(0,self.node.pager.limit,old_ids.length);
                }
                self.render_value(self.node.pager.ids);
            });

        },
        OpenObj: function(e){
            var self=this;
            e.preventDefault();
            var res_id = $(e.target).attr('data-id');
            var object = $(e.target).attr('data-obj');
            var pop = new common.FormViewDialog(this, {
                res_model: object,
                res_id:parseInt(res_id),
                context: {},
                title: _t("Open: ") + object,
                readonly:this.get("effective_readonly")
            }).open();
            pop.on('record_saved', self, function(){
                self.render_value(self.node.pager.ids);
            });

        },
        OpenRowObj: function(e){
            var self=this;
            if(!$(e.target).hasClass('open_object') && !$(e.target).hasClass('net_many_delete') && !$(e.target).closest('tr').hasClass('modify')){
                var res_id = $(e.target).closest('tr').attr('data-id');
                var object = self.field.relation;

                if(self.node.attrs.inline && !self.get("effective_readonly")){
                    
                    var old = $(e.target).closest('tbody').find('.modify');
                    $(old).removeClass('modify');
                    if(old.length>0){
                        /*restore delle righe in modifica*/
                        var model = self.field.relation;
                        var fields = self.node.attrs.net_fields;
                        var old_id = $(old).attr('data-id');
                        new Model(model).query(fields).filter([['id','=',parseInt(old_id)]]).first().then(function(result){
                            $.each(fields, function(x,field){
                                if(self.node.attrs.net_fields_property[field].type=='float'){
                                    result[field] = result[field].toLocaleString();
                                }
                                if(self.node.attrs.net_fields_property[field].type=='selection'){
                                    $.each(self.node.attrs.net_fields_property[field].selection, function(d,sel){
                                        if(sel[0]==result[field]){
                                            result[field] = sel[1];
                                        }
                                    });
                                }
                            });
                            $(old).html(QWeb.render("net2many_row", {row:result, widget:self}))
                        });
                    }
                    $(e.target).closest('tr').addClass('modify');
                    $(e.target).closest('tr').find('td').each(function(i,td){
                        self.modify_td(td);
                    })
                }else{
                    var pop = new common.FormViewDialog(this, {
                        res_model: self.field.relation,
                        res_id:parseInt(res_id),
                        context: {},
                        title: _t("Open: ") + self.string,
                        readonly:this.get("effective_readonly")
                    }).open();
                    pop.on('record_saved', self, function(){
                        self.render_value(self.node.pager.ids);
                    });
                }
            }
        },
        modify_td:function(td){
            /**carica il template in base al tipo di field per le inline**/
            var name = $(td).attr('data-name');
            var self = this;
            if(name){
                var field = self.node.attrs.net_fields_property[name].type;
                var many_field = ['one2many', 'many2many'];
                var select_type = ['selection', 'many2one'];
                if(!self.node.attrs.net_fields_property[name].readonly){
                    if(field=='one2many' || field=='many2many'){
                        /**TODO: **/
                    }else if(field=='many2one'){
                        $(td).html(QWeb.render("Net2Many_many2one_field", {value: $(td).text().trim()}));
                    }else if(field=='selection'){  
                        var selection = self.node.attrs.net_fields_property[name].selection; 
                        $(td).html(QWeb.render("Net2Many_SelectionField", {selection:selection, value:$(td).text().trim()}));
                    }else{
                        $(td).html(QWeb.render("Net2Many_InputField", {value: $(td).text().trim()}))
                    }

                }
            }
            
        },
        rewrite_input_value: function(row, result){
            /**riscrive i valori della riga, eventualmente ci fosse un onchange**/
            var self=this;
            $(row).find('td').each(function(i,td){
                var name = $(td).attr('data-name');
                if(name){
                    var field = self.node.attrs.net_fields_property[name].type;
                    var many_field = ['one2many', 'many2many'];
                    var select_type = ['selection', 'many2one'];
                    if(self.node.attrs.net_fields_property[name].readonly){
                        var old = $(td).text().trim();
                        $(td).text(result[name]);
                        if(old!=result[name]){
                            $(td).css('font-weight','bold');
                            $(td).css('color','#285F8F');
                            setTimeout(function(){ $(td).css('font-weight','normal').css('color','inherit'); }, 700);
                        }
                    }else{
                        /**TODO: FARLO ANCHE PER GLI INPUT**/
                    }
                }
            })
        },
        ModifyInput: function(e){
            /**cambia il campo e riscrive i valori**/
            var self = this;
            var new_value = $(e.target).val();
            var attr = $(e.target).closest('td').attr('data-name');
            var id = $(e.target).closest('tr').attr('data-id');
            var model = self.field.relation;
            var fields = self.node.attrs.net_fields;
            vals = {};
            vals[attr] = new_value;
            new Model(model).call('write',[parseInt(id),vals]).then(function(res){
                new Model(model).query(fields).filter([['id','=',parseInt(id)]]).first().then(function(result){
                    $.each(fields, function(x,field){
                        if(self.node.attrs.net_fields_property[field].type=='float'){
                            result[field] = result[field].toLocaleString();
                        }
                        if(self.node.attrs.net_fields_property[field].type=='selection'){
                            $.each(self.node.attrs.net_fields_property[field].selection, function(d,sel){
                                if(sel[0]==result[field]){
                                    result[field] = sel[1];
                                }
                            });
                        }
                    });
                    self.rewrite_input_value($(e.target).closest('tr'),result);
                });
            });
        },
        ModifyMany2One: function(e){
            var self=this;
            var new_id = $(e.target).closest('.net_choose_one').find('.autocomplete_go_product').attr('data-id');
            var model = self.field.relation;
            var field = $(e.target).closest('td').attr('data-name');
            var id = $(e.target).closest('tr').attr('data-id');
            var attr = {};
            var fields = self.node.attrs.net_fields;
            var text = $(e.target).text();
            attr[field] = new_id;
            new Model(model).call('write',[parseInt(id),attr]).then(function(res){
                new Model(model).query(fields).filter([['id','=',parseInt(id)]]).first().then(function(result){
                    $.each(fields, function(x,field){
                        if(self.node.attrs.net_fields_property[field].type=='float'){
                            result[field] = result[field].toLocaleString();
                        }
                        if(self.node.attrs.net_fields_property[field].type=='selection'){
                            $.each(self.node.attrs.net_fields_property[field].selection, function(d,sel){
                                if(sel[0]==result[field]){
                                    result[field] = sel[1];
                                }
                            });
                        }
                    });
                    self.rewrite_input_value($(e.target).closest('tr'),result);
                    $(e.target).closest('td').find('input').val(text)
                });
            });

        },
        ClickMany2One: function(e){
            var old = $(e.target).val();
            $(e.target).val('');
        },
        Autocomplete:function(e){
            var self=this;
            var search = $(e.target).val();
            var name = $(e.target).closest('td').attr('data-name');
            var model = self.node.attrs.net_fields_property[name].relation;
            var td = $(e.target).closest('td');
            var div = $(td).find('.autocomplete');
            var width = $(e.target).width();

            new Model(model).call('name_search',[search,[]]).then(function(results){
                if(!results){
                    $(div).html(QWeb.render("Net2Many_Autocomplete", {no_results:true}));
                }else{
                    $(div).html(QWeb.render("Net2Many_Autocomplete", {results:results, relation:model}));
                }
                $(div).width(width);
                $(div).slideDown('slow');
            });
        },
        AutocompleteNext: function(e){
            var self=this;
            e.preventDefault();
            var search = $(e.target).closest('td').find('input').val();
            if(search!=''){
                var name = $(e.target).closest('td').attr('data-name');
                var model = self.node.attrs.net_fields_property[name].relation;
                var offset = $(e.currentTarget).attr('data-off');
                new Model(model).query(['id','name','display_name']).filter([['name','ilike',search]]).offset(parseInt(offset)).limit(6).all().then(function(results){
                    var res = [];
                    $.each(results,function(i,v){
                        var obj = [v.id,v.display_name];
                        res.push(obj);
                    });
                    $(e.target).closest('.autocomplete').html(QWeb.render("Net2Many_Autocomplete", {results:res, relation:model, offset_next:parseInt(offset)+6, offset_prev:parseInt(offset)-6}))
                });
            }
        },
        AutocompletePrev: function(e){
            var self=this;
            e.preventDefault();
            var search = $(e.target).closest('td').find('input').val();
            if(search!=''){
                var name = $(e.target).closest('td').attr('data-name');
                var model = self.node.attrs.net_fields_property[name].relation;
                var offset = $(e.currentTarget).attr('data-off');
                new Model(model).query(['id','name','display_name']).filter([['name','ilike',search]]).offset(parseInt(offset)).limit(6).all().then(function(results){
                    var res = [];
                    $.each(results,function(i,v){
                        var obj = [v.id,v.display_name];
                        res.push(obj);
                    });
                    if(parseInt(offset)>0){
                        $(e.target).closest('.autocomplete').html(QWeb.render("Net2Many_Autocomplete", {results:res, relation:model, offset_next:parseInt(offset), offset_prev:parseInt(offset) - 6}))
                    }
                });
            }
        },
        Search: function(e){
            var self = this;
            var search_string = $(self.$el).find('.net_search').val();
            if(search_string==''){
                self.node.attrs.searchable_ids = false;
                return self.start();
            }
            var relation = self.field.relation;
            var fields = self.node.attrs.net_fields;
            $.each(self.node.attrs.searchable_filter,function(index,value){
                if(Array.isArray(value)){
                    /**per tipi di field diverso va semmai configurato**/
                    if(value[1] != 'ilike'){
                        value[2] = parseInt(search_string);
                    }else{
                        value[2] = search_string;
                    }
                    
                }
            });
            var filter = self.node.attrs.searchable_filter;
            var t = false;
            /**Aggiungo il campo relazionale con il collegamento al padre**/
            $.each(filter,function(i,v){
                if(v[0]==self.field.relation_field){
                    v[2]=self.getParent().datarecord.id;
                    t=true;
                }
            })
            if(!t){
                filter.push([self.field.relation_field,'=',self.getParent().datarecord.id]);
            }

            new Model(relation).query('id').filter(filter).all().then(function(results){
                var ids = [];
                $.each(results,function(i,v){
                    ids.push(v.id);
                });
                self.node.attrs.searchable_ids = ids;
                self.set_paginator(0,self.node.pager.limit,ids.length);
                self.render_value(ids);
            });

        },
        NextPage: function(e){
            var self=this;
            e.preventDefault();
            var offset = self.get_pager_value('offset') + self.get_pager_value('limit');
            self.set_paginator(offset, self.get_pager_value('limit'), self.get_pager_value('all_results'));
            self.render_value(this.node.pager.ids);
        },
        PrevPage: function(e){
            self=this;
            e.preventDefault();
            var offset = self.get_pager_value('offset') - self.get_pager_value('limit');
            self.set_paginator(offset, self.get_pager_value('limit'), self.get_pager_value('all_results'));
            self.render_value(this.node.pager.ids);
        },
        get_all_relation_objects: function(offset,limit,dial,filter){
            var self = this;
            var object = self.field.relation;
            var fields = self.node.attrs.net_fields;
            var filters = [];
            if(filter){
                filters = self.all_relation_objects_filter;
            }
            if(self.all_relation_objects_filter){
                filters = self.all_relation_objects_filter;
            }
            filters.push(['id','not in',self.get('value')]);

            if(self.node.attrs.hasOwnProperty("domain")){
                var dom = self.build_domain().eval();
                $.each(dom,function(i,v){
                    filters.push(v);
                });
            }

            new Model(object).query(fields).filter(filters).offset(offset).limit(limit).all().then(function(results){
                $.each(results,function(i,result){
                    $.each(fields, function(x,field){
                        if(self.node.attrs.net_fields_property[field].type=='float'){
                            result[field] = result[field].toLocaleString();
                        }
                        if(self.node.attrs.net_fields_property[field].type=='selection'){
                            $.each(self.node.attrs.net_fields_property[field].selection, function(d,sel){
                                if(sel[0]==result[field]){
                                    result[field] = sel[1];
                                }
                            });
                        }
                    });
                });
                self.all_relation_objects = results;
                dial.$el.html(QWeb.render("net_2_many_all_relation_tbody", {widget: self, offset:offset, all:results.length, limit:limit}));
                $(dial.$el).find('.next_page').click(function(){
                    self.get_all_relation_objects(offset+limit,limit,dial,false);
                });
                $(dial.$el).find('.prev_page').click(function(){
                    self.get_all_relation_objects(offset-limit,limit,dial,false);
                });
                $(dial.$el).find('.net_row').click(function(){
                    self.add_row(this);
                });
                $(dial.$el).find('.net_button_search').click(function(){
                    var search_string = $(dial.$el).find('.net_search').val();
                    var relation = self.field.relation;
                    var fields = self.node.attrs.net_fields;
                    $.each(self.node.attrs.searchable_filter,function(index,value){
                        if(Array.isArray(value)){
                            if(value[1] != 'ilike'){
                                value[2] = parseInt(search_string)
                            }else{
                                value[2] = search_string;
                            }
                            
                        }
                    });
                    var f = self.node.attrs.searchable_filter;
                    self.all_relation_objects_filter = f;
                    if(search_string==''){
                        self.get_all_relation_objects(0,20,dial,false);
                        self.all_relation_objects_filter = false;
                    }else{
                        self.get_all_relation_objects(0,20,dial,true);
                    }
                    
                });
            });
        },
        add_row: function(row){
            var id = $(row).attr('data-id');
            var self=this;
            var ids = self.get('value');
            if(!ids){
                ids=[];
            }

            ids.unshift(parseInt(id));
            
            self.internal_set_value(ids);

            if(!self.getParent().datarecord.hasOwnProperty('id')){
                self.set_paginator(0,20,ids.length);
            }else{
                self.set_paginator(0,self.node.pager.limit,ids.length);
            }
            
            self.render_value(self.node.pager.ids);
           
            $(row).remove();
        },
        Delete_Row: function(e){
            var self = this;
            var id = parseInt($(e.target).closest('tr').attr('data-id'));
            var values = self.get('value');
            var index = values.indexOf(id);
            if (index > -1) {
                values.splice(index, 1);
            }
            self.deleted_row.push(parseInt(id));
            $(e.target).closest('tr').remove();
            self.set_paginator(self.node.pager.offset,self.node.pager.limit,values.length);
            self.render_value(self.node.pager.ids);
        },
        construct_net_fields: function(all_fields){
            /**costruisce le proprietà dei fileds richiesti in vista**/
            var self = this;
            var relation = self.field.relation;
            self.node.attrs.net_fields_property = {};
            $.each(self.node.attrs.net_fields, function(index, field){
                if(field in all_fields){
                    self.node.attrs.net_fields_property[field] = all_fields[field];
                }
            }); 
        },
        construct_searchable_filter: function(searchable_fields, all_fields){
            /**
            Costruisce il dominio per i filtri di ricerca
            Param:
              searchable_fields: array di field searchable
              all_fields: tutti i fields dell'oggetto della relazione
            **/
            var self = this;
            self.node.attrs.searchable_filter = [];

            for (i = 1; i <= searchable_fields.length - 1; i++) {
                /**essendo una ricerca su vari fields mette gli 'or' per la costruzione del dominio**/ 
                self.node.attrs.searchable_filter.push('|');
            }

            $.each(searchable_fields, function(index, field){
                /**se è un campo di un altro field relation interno**/
                var field_split = field.split('.');

                if(field_split[0] in all_fields){
                    if('relation' in all_fields[field_split[0]]){
                        /**è un field relation**/
                        new Model(all_fields[field_split[0]]['relation']).call('fields_get',[]).then(function(res_second_fields){
                            if(field_split[1] in res_second_fields){
                                var domain = self.construct_domain(field,res_second_fields[field_split[1]].type);
                                self.node.attrs.searchable_filter.push(domain);
                            }
                        });
                    }else{
                        var domain = self.construct_domain(field,all_fields[field_split[0]].type);
                        self.node.attrs.searchable_filter.push(domain);
                    }
                }
            });
        },
        construct_domain: function(name,type){
            var operator = 'ilike';
            var value = '';
            if(type == 'integer'){
                operator = '=';
                value = 0;
            }
            if(type == 'float'){
                operator = '=';
                value = 0;
            }
            /**per altri campi modificare qua il dominio**/
            return [name,operator,value];
        },
        set_paginator: function(offset, limit, all_results){
            /**setta il paginatore**/
            this.node.pager.limit = limit;
            this.node.pager.offset = offset;
            this.node.pager.all_results = all_results;
            this.node.pager.pages = Math.floor(this.node.pager.all_results / this.node.pager.limit) + 1;
            this.node.pager.min = this.node.pager.offset + 1;
            this.node.pager.max = this.node.pager.offset + this.node.pager.limit;
            if(this.node.pager.max > this.node.pager.all_results){
                this.node.pager.max = this.node.pager.all_results;
            }
            /*recupera gli id per la pagina corrente*/
            if(this.node.attrs.searchable_ids){
                this.node.pager.ids = this.node.attrs.searchable_ids.slice(offset,this.node.pager.max)
            }else{
                var values = this.get('value');
                if(values){
                    this.node.pager.ids = values.slice(offset,this.node.pager.max);
                }
            }
        },
        get_pager_value: function(attr){
            if(!this.node.pager.hasOwnProperty(attr)){
                return false;
            }
            return this.node.pager[attr];
        },
        get_pager: function(){
            return this.node.pager;
        },
    });

    core.form_widget_registry.add('net_2many', Net2Many);
});

