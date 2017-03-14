odoo.define('netaddiction_warehouse.inventory_reports', function (require) {
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
    var QWeb = core.qweb;
    var common = require('web.form_common');

    var InventoryReports = Widget.extend({
        init: function(parent){
            var self = this;
            this._super(parent);
            self.company_id = parseInt(session.company_id);
            new Model('stock.location').query().filter([['company_id','=',self.company_id],['active','=',true],['usage','=','internal'],['name','=','Stock']]).first().then(function(location){
                self.wh = parseInt(location.id);
            });
            self.offset = 0;
            self.limit = 100;
            self.all = 0;
            self.order_by = 'name';
            self.values = false;
            self.suppliers_results = false;
            self.categ_filter = false;
            self.suppliers_pids = false;
            self.supplier = false;
            self.category = false;
            self.attribute = false;
            self.attribute_filter = false;
        },
        events: {
            'click .next_page': 'NextPage',
            'click .prev_page': 'PrevPage',
            'change #categories': 'ChangeCategory',
            'change #suppliers': 'ChangeSuppliers',
            'click #get_inventory_value': 'get_inventory_values',
            'click .open_product': 'OpenProduct',
            'change #attributes': 'ChangeAttributes',
            'click .export_csv': 'ExportCsv'
        },
        start: function(){
            var self = this;
            self.get_products(false);
            //self.get_inventory_values();
            self.$el.html(QWeb.render("inventory_reports_base", {widget: self}));
            self.construct_categories();
            self.construct_suppliers();
            self.construct_attributes();
        },
        ExportCsv: function(e){
            var self = this;
            var filter = [['product_wh_location_line_ids','!=',false],['company_id','=',self.company_id]];
            var rep = false;
            if(self.categ_filter){
                filter.push(self.categ_filter);
            }
            if(self.suppliers_pids){
                filter.push(['id','in',self.suppliers_pids]);
                rep = self.suppliers_results[self.supplier];
            }
            if(self.attribute_filter){
                filter.push(self.attribute_filter)
            }
            new Model('stock.quant').call('reports_inventario',[filter,rep]).then(function(id){
                var pop = new common.FormViewDialog(this, {
                    res_model: 'ir.attachment',
                    res_id:parseInt(id),
                    context: {},
                    title: _t("Apri: Csv"),
                    readonly:true
                }).open();
            })
        },
        OpenProduct: function(e){
            e.preventDefault();
            var res_id = parseInt($(e.currentTarget).attr('data-id'));
            var pop = new common.FormViewDialog(this, {
                res_model: 'product.product',
                res_id:res_id,
                context: {},
                title: _t("Apri: Prodotto"),
                readonly:true
            }).open();
        },
        ChangeCategory: function(e){
            var self = this;
            self.$el.find('#inventory_value').html(QWeb.render("InventoryValueLoading", {}));
            
            self.offset = 0;
            var value = parseInt($('#categories').val());
            if(value==1){
                self.categ_filter = false;
                self.category = false;
                self.get_products();
            }else{
                self.categ_filter = ['categ_id','=',value];
                self.category = value;
                self.get_products();
            }
            //self.get_inventory_values();
        },
        ChangeSuppliers: function(e){
            var self = this;
            self.$el.find('#inventory_value').html(QWeb.render("InventoryValueLoading", {}));

            var value = parseInt($('#suppliers').val());
            self.supplier = value;
            if(value==0){
                self.supplier=false;
                self.suppliers_pids=false;
                self.get_products();
            }else{
                /**fa una query perchè usa le stock.quant e non i product**/
                if(self.suppliers_results){
                    if(value in self.suppliers_results){
                        self.suppliers_pids = self.suppliers_results[value]['pids'];
                        self.get_products();
                        //self.get_inventory_values();                    
                    }else{
                        self.get_suppliers_products(value);
                    }
                }else{
                    self.get_suppliers_products(value);
                }
            }
        },
        ChangeAttributes: function(e){
            var self = this;
            self.$el.find('#inventory_value').html(QWeb.render("InventoryValueLoading", {}));

            var value = parseInt($('#attributes').val());
            self.attribute = value;
            if(value==0){
                self.attribute=false;
                self.attribute_filter=false;
                self.get_products();
            }else{
                self.attribute_filter = ['attribute_value_ids','=',value];
                self.attribute = value;
                self.get_products();
            }
        },
        get_suppliers_products: function(value){
            var self = this;
            if(!self.suppliers_results){
                self.suppliers_results = {};
            }
            
            self.suppliers_results[value] = {};
            self.suppliers_results[value]['pids'] = [];
            self.suppliers_results[value]['products'] = {};
            var filter = [['company_id','=',self.company_id],['location_id','=',self.wh],['history_ids.picking_id.partner_id.id','=',value]];
            new Model('stock.quant').query(['inventory_value','qty']).filter(filter).group_by('product_id').then(function(results){
                var total_inventory = 0;
                $.each(results,function(i,v){
                    total_inventory = total_inventory + v.attributes.aggregates.inventory_value;
                    self.suppliers_results[value]['pids'].push(v.attributes.value[0]);
                    self.suppliers_results[value]['products'][v.attributes.value[0]] = {'qty': v.attributes.aggregates.qty, 'inventory_value': v.attributes.aggregates.inventory_value};
                });
                self.suppliers_pids = self.suppliers_results[value]['pids'];
                self.get_products();
                //self.get_inventory_values();
            });
        },
        NextPage: function(e){
            var self=this;
            e.preventDefault();
            self.offset = self.offset + self.limit;
            var domain = false;
            /**domain TODO**/
            self.get_products(domain);
        },
        PrevPage: function(e){
            var self=this;
            e.preventDefault();
            self.offset = self.offset - self.limit;
            var domain = false;
            /**domain TODO**/
            self.get_products(domain);
        },
        get_inventory_values: function(e){
            e.preventDefault();
            var self = this;
            var fields = ['med_inventory_value','qty_available'];
            var filter = [['product_wh_location_line_ids','!=',false],['company_id','=',self.company_id]];
            if(self.categ_filter){
                filter.push(self.categ_filter);
            }
            if(self.suppliers_pids){
                filter.push(['id','in',self.suppliers_pids]);
            }
            if(self.attribute_filter){
                filter.push(self.attribute_filter)
            }
            new Model('product.product').query(fields).filter(filter).all().then(function(results){
                var value = 0;
                $.each(results,function(i,v){
                    if(self.suppliers_pids){
                        value = value + self.suppliers_results[self.supplier]['products'][v.id]['inventory_value'];
                    }else{
                        value = value + (v.qty_available * v.med_inventory_value);
                    }
                });
                self.$el.find('#inventory_value').html(QWeb.render("InventoryValue", {value: value.toLocaleString()}));
            })
        },
        get_products: function(){
            var self=this;
            var fields = ['id', 'barcode', 'display_name', 'categ_id', 'med_inventory_value', 'med_inventory_value_intax', 'qty_available', 'qty_available_now', 'product_wh_location_line_ids', 'intax_price', 'offer_price'];
            var filter = [['product_wh_location_line_ids','!=',false],['company_id','=',self.company_id]];
            if(self.categ_filter){
                filter.push(self.categ_filter);
            }
            if(self.suppliers_pids){
                filter.push(['id','in',self.suppliers_pids]);
            }
            if(self.attribute_filter){
                filter.push(self.attribute_filter)
            }
            new Model('product.product').query(fields).filter(filter).offset(self.offset).limit(self.limit).order_by(self.order_by).all().then(function(products){
                var new_products = [];
                $.each(products, function(i,product){
                    product['total_inventory'] = (product.med_inventory_value * product.qty_available).toLocaleString();
                    product.med_inventory_value = product.med_inventory_value.toLocaleString();
                    if(product.offer_price){
                        product.price = product.offer_price.toLocaleString();
                    }else{
                        product.price = product.intax_price.toLocaleString();
                    }
                    if(self.suppliers_pids){
                        product.qty_available = self.suppliers_results[self.supplier]['products'][product.id]['qty'];
                        product['total_inventory'] = self.suppliers_results[self.supplier]['products'][product.id]['inventory_value'].toLocaleString();
                    }
                });
                self.$el.find('#inventory_table').html(QWeb.render("InventoryTableProducts", {products: products}));
                framework.unblockUI();
                self.set_height();
                self.set_pager();
            });
            new Model('product.product').query(['id']).filter(filter).count().then(function(count){
                self.all = parseInt(count);
            });
        },
        set_height: function(){
            var self = this;
            var h = self.$el.find('#inventory_top_block').outerHeight();
            var theadH = self.$el.find('#inventory_table thead').outerHeight();
            var topH = $('#oe_main_menu_navbar').outerHeight();
            self.$el.find('#inventory_top_block').css('top',topH);
            self.$el.find('#inventory_table thead').css('position','fixed').css('width','100%').css('top',h+topH)
            self.$el.find('#inventory_table').css('margin-top',h+theadH);

            var row = self.$el.find('#inventory_table tbody tr').first();
            $(row).find('td').each(function(i,v){
                var id = $(v).attr('data-id');
                var width = $(v).outerWidth();
                $('#'+id).outerWidth(width);
            });
        },
        construct_categories: function(){
            var self=this;
            new Model('product.category').query([]).filter([['company_id','=',self.company_id]]).all().then(function(categories){
                self.$el.find('#categories').html(QWeb.render("CategoriesSelect", {categories: categories}));
            });
        },
        construct_suppliers: function(){
            var self=this;
            new Model('res.partner').query(['id','name']).filter([['supplier','=',true],['parent_id','=',false],['active','=',true],['company_id','=',self.company_id]]).order_by('name').all().then(function(suppliers){
                self.$el.find('#suppliers').html(QWeb.render("SuppliersSelect", {suppliers: suppliers}));
            });
        },
        construct_attributes: function(){
            var self=this;
            new Model('product.attribute.value').query(['id','display_name']).filter([['company_id','=',self.company_id]]).order_by('attribute_id','name').all().then(function(attributes){
                self.$el.find('#attributes').html(QWeb.render("AttributesSelect", {attributes: attributes}));
            });
        },
        set_pager: function(){
            var self = this;
            self.$el.find('#from').text(self.offset);
            var to = parseInt(self.offset) + parseInt(self.limit);
            self.$el.find('#to').text(to);
            self.$el.find('#all').text(self.all);

            if(self.offset <= 0){
                self.$el.find('.prev_page').hide();
            }else{
                self.$el.find('.prev_page').show();
            }
            if(to >= self.all){
                self.$el.find('.next_page').hide();
                self.$el.find('#to').text(self.all);
            }else{
                self.$el.find('.next_page').show();
            }
        }
    });

    core.action_registry.add("netaddiction_warehouse.inventory_reports", InventoryReports);
})