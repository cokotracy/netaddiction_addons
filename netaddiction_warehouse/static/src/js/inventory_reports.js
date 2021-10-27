odoo.define('netaddiction_warehouse.inventory_reports', function (require) {
"use strict";

    var core = require('web.core');
    var framework = require('web.framework');
    var session = require('web.session');
    var Widget = require('web.Widget');
    var _t = core._t;
    var QWeb = core.qweb;
    // var common = require('web.form_common');
    var common = require('web.view_dialogs');

    // New requirements
    var AbstractAction = require('web.AbstractAction');

    //unused things
    /*var web_client = require('web.web_client');
    var Dialog = require('web.Dialog');
    var Notification = require('web.Notification');
    var Class = require('web.Class');
    var Pager = require('web.Pager');
    var ActionManager = require('web.ActionManager');*/

    //deprecated
    //var Model = require('web.DataModel');


    var InventoryReports = AbstractAction.extend({
        init: function(parent, action, options){
            var self = this;
            this._super.apply(this, arguments);
            self.company_id = parseInt(session.company_id);

            this._rpc({
                model: 'stock.location',
                method: 'search_read',
                fields: [
                    'id',
                    'name'
                ],
                domain: [
                    ['company_id','=',self.company_id],
                    ['active','=',true],
                    ['usage','=','internal'],
                    ['name','=','Stock']
                ],
                limit: 1,
            }).then(function (location) {
                if (location != null && location.length > 0) {
                    self.wh = parseInt(location[0].id);
                }
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

            self.available_deactive = false;
            self.supplier_available_deactive = false;
            self.supplier_zero_negative_active = false;
        },
        events: {
            'click .next_page': 'NextPage',
            'click .prev_page': 'PrevPage',
            'change #categories': 'ChangeCategory',
            'change #suppliers': 'ChangeSuppliers',
            'click #get_inventory_value': 'get_inventory_values',
            'click .open_product': 'OpenProduct',
            'change #attributes': 'ChangeAttributes',
            'click .export_csv': 'ExportCsv',
            'click #available_deactive': 'Available_deactive',
            'click #supplier_available_deactive': 'Supplier_available_deactive',
            'click #supplier_zero_negative_active': 'Supplier_zero_negative_active',
            'click .activate_p': 'activate_product',
            'click .deactivate_p': 'deactivate_product',
        },
        start: function(){
            var self = this;
            //self.get_inventory_values();
            var active_id = parseInt(session.active_id);

            this._rpc({
                model: 'ir.model.data',
                method: 'search_read',
                fields: ['complete_name'],
                domain: [
                    ['res_id','=',active_id],
                    ['model','=','ir.ui.menu']
                ],
                limit: 1,
            }).then(function (menu) {
                if (menu && menu.length > 0) {
                    if (menu[0].complete_name == 'netaddiction_warehouse.products_problem') {
                        self.$el.html(
                            QWeb.render(
                                "inventory_reports_base",
                                {
                                    widget: self,
                                    is_problematic: true
                                }
                            )
                        );
                        self.available_deactive = true;
                        self.get_products(false);
                    } else {
                        self.get_products(false);
                        self.$el.html(
                            QWeb.render(
                                "inventory_reports_base",
                                {widget: self}
                            )
                        );
                    }
                } else {
                    self.get_products(false);
                    self.$el.html(
                        QWeb.render(
                            "inventory_reports_base",
                            {widget: self}
                        )
                    );
                }
            });

            self.construct_categories();
            self.construct_suppliers();
            self.construct_attributes();
        },
        Available_deactive: function(){
            this.supplier_available_deactive = false;
            this.supplier_zero_negative_active = false;
            this.available_deactive = true;
            this.get_products(false);
        },
        Supplier_available_deactive: function(){
            this.available_deactive = false;
            this.supplier_available_deactive = true;
            this.supplier_zero_negative_active = false;
            this.get_products(false);
        },
        Supplier_zero_negative_active: function(){
            this.available_deactive = false;
            this.supplier_available_deactive = false;
            this.supplier_zero_negative_active = true;
            this.get_products(false);
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
            this._rpc({
                model: 'stock.quant',
                method: 'reports_inventario',
                args: [
                    filter,
                    rep,
                ],
            }).then(function (id) {
                var pop = new common.FormViewDialog(this, {
                    res_model: 'ir.attachment',
                    res_id:parseInt(id),
                    context: {},
                    title: _t("Apri: Csv"),
                    readonly:true
                }).open();
            });
        },
        OpenProduct: function(e){
            e.preventDefault();
            var res_id = parseInt($(e.currentTarget).attr('data-id'));
            var pop = new common.FormViewDialog(this, {
                res_model: 'product.product',
                res_id:res_id,
                context: {},
                title: _t("Apri: Prodotto"),
                readonly:false
            }).open();
        },
        ChangeCategory: function(e){
            var self = this;
            self.$el.find('#inventory_value').html(
                QWeb.render("InventoryValueLoading", {})
            );
            
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
            self.$el.find('#inventory_value').html(
                QWeb.render("InventoryValueLoading", {})
            );

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
            self.$el.find('#inventory_value').html(
                QWeb.render("InventoryValueLoading", {})
            );

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
            var filter = [
                ['company_id','=',self.company_id],['location_id','=',self.wh],
                // FIXME: history_ids non esiste più
                // ['history_ids.picking_id.partner_id.id','=',value]
            ];

            this._rpc({
                model: 'stock.quant',
                method: 'search_read',
                fields: [
                    'inventory_value',
                    'qty'
                ],
                domain: filter,
                group_by: ['product_id'],
            }).then(function (results) {
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

            this._rpc({
                model: 'product.product',
                method: 'search_read',
                fields: fields,
                domain: filter,
                groupBy: ['product_id'],
            }).then(function (results) {
                var value = 0;
                $.each(results,function(i,v){
                    if(self.suppliers_pids){
                        value = value + self.suppliers_results[self.supplier]['products'][v.id]['inventory_value'];
                    }else{
                        value = value + (v.qty_available * v.med_inventory_value);
                    }
                });
                self.$el.find('#inventory_value').html(
                    QWeb.render(
                        "InventoryValue",
                        {value: value.toLocaleString()}
                    )
                );
            });
        },
        activate_product: function(e){
            e.preventDefault();
            var self = this;
            var id = $(e.currentTarget).closest('tr').find('.open_product').attr('data-id');
            var row = $(e.currentTarget).closest('tr');

            this._rpc({
                model: 'product.product',
                method: 'write',
                args: [
                    [parseInt(id)],
                    {'sale_ok': true}
                ],
            }).then(function () {
                row.remove();
            });
        },
        deactivate_product: function(e){
            e.preventDefault();
            var self = this;
            var id = $(e.currentTarget).closest('tr').find('.open_product').attr('data-id');
            var row = $(e.currentTarget).closest('tr');

            this._rpc({
                model: 'product.product',
                method: 'write',
                args: [
                    [parseInt(id)],
                    {'sale_ok': false}
                ],
            }).then(function () {
                row.remove();
            });
        },
        get_products: function(){
            var self=this;
            // var fields = ['id', 'barcode', 'display_name', 'categ_id', 'med_inventory_value', 'med_inventory_value_intax', 'qty_available', 'qty_available_now', 'product_wh_location_line_ids', 'intax_price', 'offer_price'];
            var fields = ['id', 'barcode', 'display_name', 'categ_id', 'med_inventory_value', 'med_inventory_value_intax', 'qty_available', 'qty_available_now'];
            // var filter = [['product_wh_location_line_ids','!=',false],['company_id','=',self.company_id]];
            // var fields = ['id', 'barcode', 'display_name', 'categ_id']
            var filter = [['active', '=', true]]
            /**mi immetto qua per cambiare i filtri per i prodotti problematici**/
            if(self.available_deactive){
                var text = 'Prodotti Problematici - In Magazzino, Spenti';
                $('.breadcrumb li').text(text);
                filter = [['product_wh_location_line_ids','!=',false],['company_id','=',self.company_id], ['sale_ok','=',false]];
            }
            if(self.supplier_available_deactive){
                var text = 'Prodotti Problematici - Disponibili al fornitore, qty <= 0, spenti';
                $('.breadcrumb li').text(text);
                filter = [['qty_available','<=',0],['seller_ids.avail_qty','>',0], ['company_id','=',self.company_id], ['sale_ok','=',false]];
            }

            if(self.categ_filter){
                filter.push(self.categ_filter);
            }
            if(self.suppliers_pids){
                filter.push(['id','in',self.suppliers_pids]);
            }
            if(self.attribute_filter){
                filter.push(self.attribute_filter);
            }

            if(self.supplier_zero_negative_active){
                var text = 'Prodotti Problematici - Qty <= 0, accesi, non in prenotazione, fornitore a zero';
                $('.breadcrumb li').text(text);

                this._rpc({
                    model: 'product.product',
                    method: 'problematic_product',
                    args: [],
                }).then(function (results) {
                    self.all = parseInt(results.length);
                    var ids = results.splice(self.offset, self.limit);

                    this._rpc({
                        model: 'product.product',
                        method: 'search_read',
                        fields: fields,
                        domain: [
                            ['id','in',ids]
                        ],
                    }).then(function (products) {
                        var new_products = [];
                        $.each(products, function(i,product){
                            product['total_inventory'] = (product.med_inventory_value * product.qty_available).toLocaleString();
                            product.med_inventory_value = product.med_inventory_value.toLocaleString();
                            // if(product.offer_price){
                            //     product.price = product.offer_price.toLocaleString();
                            // }else{
                            //     product.price = product.intax_price.toLocaleString();
                            // }
                            product.price = "0";
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

                });
            }else{
                this._rpc({
                    model: 'product.product',
                    method: 'search_read',
                    fields: fields,
                    domain: filter,
                    offset: self.offset,
                    limit: self.limit,
                    //orderBy: self.order_by,
                }).then(function (products) {
                    var new_products = [];
                    $.each(products, function(i,product){
                        product['total_inventory'] = (product.med_inventory_value * product.qty_available).toLocaleString();
                        product.med_inventory_value = product.med_inventory_value.toLocaleString();
                        // if(product.offer_price){
                        //     product.price = product.offer_price.toLocaleString();
                        // }else{
                        //     product.price = product.intax_price.toLocaleString();
                        // }
                        product.price = "0";
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

                this._rpc({
                    model: 'product.product',
                    method: 'search_count',
                    args: [filter],
                }).then(function (count) {
                    self.all = parseInt(count);
                });
            }

            
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
            this._rpc({
                model: 'product.category',
                method: 'search_read',
                domain: [
                    ['id', '!=', 0]
                ],
            }).then(function (categories) {
                self.$el.find('#categories').html(
                    QWeb.render("CategoriesSelect", {categories: categories})
                );
            });
        },
        construct_suppliers: function(){
            var self=this;
            this._rpc({
                model: 'res.partner',
                method: 'search_read',
                fields: [
                    'id',
                    'name'
                ],
                domain: [
                    ['supplier','=',true],
                    ['parent_id','=',false],
                    ['active','=',true],
                    ['company_id','=',self.company_id]
                ],
            }).then(function (suppliers) {
                self.$el.find('#suppliers').html(
                    QWeb.render("SuppliersSelect", {suppliers: suppliers})
                );
            });
        },
        construct_attributes: function(){
            var self=this;
            this._rpc({
                model: 'product.attribute.value',
                method: 'search_read',
                fields:[
                    'id',
                    'display_name'
                ],
                domain: [
                    ['id','!=',0]
                ],
                // orderBy: [
                //     'attribute_id',
                //     'name'
                // ],
            }).then(function (attributes) {
                self.$el.find('#attributes').html(
                    QWeb.render("AttributesSelect", {attributes: attributes})
                );
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