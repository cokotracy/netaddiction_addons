odoo.define('netaddiction_purchase_orders.products_to_buy', function (require) {
    "use strict";

    var core = require('web.core');
    var session = require('web.session');
    var Widget = require('web.Widget');
    var AbstractAction = require('web.AbstractAction');

    var ProductList = AbstractAction.extend({
        init: function (parent, action, options) {
            this._super.apply(this, arguments);
            this.action = action;
            this.action_manager = parent;
        },
        start: function () {
            this._super.apply(this, arguments);
            var self = this;
            this._rpc({
                model: 'product.product',
                method: 'get_qty_available_negative',
                args: [false, false, session.user_context],
            }).then((products)=>{
                self._rpc({
                    model: 'res.partner',
                    method: 'get_all_suppliers',
                    args: [],
                }).then((suppliers)=>{
                    self._rpc({
                        model: 'product.category',
                        method: 'get_all_categories',
                        args: [],
                    }).then((categories)=>{
                        var list = new List(self, products, suppliers, categories);
                        self.$el.html('');
                        return list.appendTo(self.$el);
                    });
                });
            });
        },
    });

    // TODO this Widget seems to be unused, can we remove it?
    var SearchInput = Widget.extend({
        template: "search_input",
        init: function (parent, search) {
            this._super.apply(this, arguments);
            this.search = search;
        },
    });

    var List = Widget.extend({
        template: "purchase_product_list",
        events: {
            "change #search": "doFilterALL",
            // TODO is this necessary? The SearchInput Widget seems to be useless
            "click .purchase_input_remove": "doActionRemove",
            "click .purchase_link_product": "doOpenProduct",
            "click .purchase_link_incoming": "doOpenIncoming",
            "click .purchase_link_outgoing": "doOpenOutgoing",
            "click .purchase_select_all": "doSelectAll",
            "change #search_supplier": "doFilterSupplier",
            "change .supplier": "doSelectTr",
            "click #send_to_purchase": "doSendToOrder",
            "change #search_categories": "doSearchCategories",
            'change #search_available': 'doFilterALL',
            'change #search_pren': 'doFilterALL'
        },
        init: function (parent, products, suppliers, categories) {
            this._super(parent);
            this.products = products;
            this.suppliers = suppliers;
            this.categories = categories;
        },
        doSearchCategories: function (e) {
            var cat_id = $(e.currentTarget).val();
            var domain = { 'categories': cat_id }
            this.doFilterALL(domain)
        },
        doFilterALL: function (domain) {
            //tutte in and
            var cat_id = $('#search_categories').val()
            var sup_id = $('#search_supplier').val()
            var qta_id = $('#search_available').val()
            var pren = $('#search_pren').val()
            var search = $('#search').val()

            $(this.products).each(function (index, value) {
                var cat_visible = 1
                if (cat_id != null) {
                    if (parseInt(value.category) == parseInt(cat_id)) {
                        cat_visible = 1
                    } else {
                        cat_visible = 0
                    }
                }
                if (cat_id == 1) {
                    cat_visible = 1
                }
                var sup_visible = 0
                if (sup_id != null) {
                    $(value.seller_ids).each(function (id, seller) {
                        if (parseInt(sup_id) == parseInt(seller.id)) {
                            sup_visible = 1
                            $('.supplier_code_' + value.id).text(seller.product_code)
                        }
                    })
                    if (sup_id == 'all') {
                        sup_visible = 1
                        $('.supplier_code_' + value.id).text('')
                    }
                } else {
                    sup_visible = 1
                }
                var qta_visible = 1
                var qta_prev = value.qty_available - value.outgoing_qty + value.incoming_qty

                if (parseInt(qta_id) == 0 && parseInt(qta_prev) != 0) {
                    qta_visible = 0
                }
                if (parseInt(qta_id) == 1 && parseInt(qta_prev) < 0) {
                    qta_visible = 0
                }
                if (parseInt(qta_id) == 2 && parseInt(qta_prev) >= 0) {
                    qta_visible = 0
                }
                var qta_pren = 1
                if (pren == 0 && new Date(value.out_date).getTime() > new Date().getTime()) {
                    qta_pren = 0
                }
                var barcode_visible = 1
                if (search != '') {
                    if (value.barcode != search) {
                        barcode_visible = 0
                    }
                }
                if (sup_visible == 1 && cat_visible == 1 && qta_visible == 1 && qta_pren == 1 && barcode_visible == 1) {
                    $('#pid_' + value.id).show()
                    if (sup_id != null && sup_id != 'all') {
                        $('#pid_' + value.id).find('.product_selector').prop('checked', true);
                        $('#pid_' + value.id).find('.supplier').val(sup_id);
                    }
                    if (sup_id == 'all' || sup_id == null) {
                        $('#pid_' + value.id).find('.product_selector').prop('checked', false);
                        $('#pid_' + value.id).find('.supplier').val('');
                    }
                } else {
                    $('#pid_' + value.id).hide()
                }
            })
        },
        doActionSearch: function (e) {
            var search = this.$(e.currentTarget).val();
            var sup_id = $('#search_supplier').val();
            var domain = [search, false]
            var self = this
            this._rpc({
                model: 'product.product',
                method: 'get_qty_available_negative',
                args: domain,
            }).then((products)=>{
                self._rpc({
                    model: 'res.partner',
                    method: 'get_all_suppliers',
                    args: [],
                }).then((suppliers)=>{
                    self._rpc({
                        model: 'product.category',
                        method: 'get_all_categories',
                        args: [],
                    }).then((categories)=>{
                        $('.oe_client_action').html('');
                        var list = new List(self, products, suppliers, categories);
                        return list.appendTo('.oe_client_action');
                    });
                });
            });
        },
        // TODO is this necessary?
        doActionRemove: function (e) {
            this.$(e.currentTarget).closest('.oe_searchview_facet').remove();
            var sup_id = $('#search_supplier').val();
            var domain = [false, false]
            if (sup_id != null) {
                domain = [false, sup_id]
            }
            $('.oe_client_action').html('');
            this._rpc({
                model: 'product.product',
                method: 'get_qty_available_negative',
                args: domain,
            }).then((products)=>{
                self._rpc({
                    model: 'res.partner',
                    method: 'get_all_suppliers',
                    args: [],
                }).then((suppliers)=>{
                    var list = new List(self, products, suppliers);
                    // TODO check this oe_client_action appendTo
                    list.appendTo('.oe_client_action');
                    if (sup_id != '') {
                        $('#search_supplier').val(sup_id);
                        $('.product_selector').prop('checked', true);
                        $('.supplier').val(sup_id);
                    }
                });
            });
        },
        doOpenProduct: function (e) {
            e.preventDefault();
            var id = $(e.currentTarget).closest('tr').attr('data-id')
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "product.product",
                res_id: parseInt(id),
                views: [[false, 'form']],
                target: 'new',
                context: {},
                flags: { 'form': { 'action_buttons': true } }
            });
        },
        doOpenIncoming: function (e) {
            e.preventDefault();
            var pid = $(e.currentTarget).closest('tr').attr('data-id')
            var name = $(e.currentTarget).closest('tr').find('.purchase_link_product').text()
            var title = 'Ordini di Acquisto per ' + name
            this.do_action({
                type: 'ir.actions.act_window',
                name: title,
                res_model: 'purchase.order.line',
                views: [[false, 'list'], [false, 'search']],
                target: 'new',
                context: {},
                domain: [['product_id', '=', parseInt(pid)], ['state', '=', 'purchase']]
            });
        },
        doOpenOutgoing: function (e) {
            e.preventDefault();
            var pid = $(e.currentTarget).closest('tr').attr('data-id')
            var name = $(e.currentTarget).closest('tr').find('.purchase_link_product').text()
            var title = 'Ordini in Uscita per ' + name
            this.do_action({
                name: title,
                type: 'ir.actions.act_window',
                res_model: "sale.order.line",
                views: [[false, 'list'], [false, 'search']],
                target: 'new',
                context: {},
                domain: [['product_id', '=', parseInt(pid)], ['state', 'in', ['sale', 'partial_done', 'problem']]]
            });
        },
        doSelectAll: function (e) {
            var checked = $(e.currentTarget).is(':checked');
            if (checked) {
                $('.product_selector').prop('checked', true);
            } else {
                $('.product_selector').prop('checked', false);
            }
        },
        doFilterSupplier: function (e) {
            var sup_id = $(e.currentTarget).val();
            var search = $('.oe_facet_value').text().trim();
            // NOTE: Code commented by NA
            /*var domain = [false,sup_id]
            if (search!=''){
                domain = [search,sup_id]
            }*/

            var domain = { 'supplier': sup_id }
            this.doFilterALL(domain)
            // NOTE: Code commented by NA
            /*return new instance.web.Model('product.product').call('get_qty_available_negative',domain).then(function(products){
                new instance.web.Model('res.partner').call('get_all_suppliers').then(function(suppliers){
                    $('.oe_client_action').html('');
                    var list = new local.List(self,products,suppliers);
                    list.appendTo('.oe_client_action');
                    $('#search_supplier').val(sup_id);
                    $('.supplier').val(sup_id);
                    if(sup_id != 'all'){
                        $('.product_selector').prop('checked',true);
                    }
                    
                    if (search!=''){
                        var input = new local.SearchInput(self,search)
                        input.insertBefore('#search')
                    }
                })
            });**/
        },
        doSelectTr: function (e) {
            if ($(e.currentTarget).val() != '') {
                $(e.currentTarget).closest('tr').find('.product_selector').prop('checked', true);
            } else {
                $(e.currentTarget).closest('tr').find('.product_selector').prop('checked', false);
            }

        },
        doSendToOrder: function (e) {
            var select = new Array();
            var count = 0;
            var self = this;
            $('.product_selector').each(function (index, value) {
                if ($(value).is(':checked')) {
                    if ($(value).closest('tr').find('.supplier').val() != '' && $(value).closest('tr').find('.qty_order').val() > 0) {
                        select.push(value);
                    }
                    count = count + 1;
                }
            })

            if (select.length == 0 || select.length < count) {
                return self.do_warn('Errore', 'Controlla i dati inseriti: hai dimenticato un fornitore o una selezione oppure hai inserito una quantità da ordinare negativa');
            } else {
                var products = [];
                $(select).each(function (index, value) {
                    var qty_order = $(value).closest('tr').find('.qty_order').val();
                    var supplier = $(value).closest('tr').find('.supplier').val();
                    var product_id = $(value).closest('tr').attr('data-id');
                    products.push([product_id, supplier, qty_order]);
                });
                self._rpc({
                    model: 'purchase.order',
                    method: 'put_in_order',
                    args: [products],
                }).then((result)=>{
                    $(select).each(function (index, value) {
                        var tr = $(value).closest('tr');
                        $(tr).remove()
                    })
                    self.do_notify('Successo', 'I prodotti sono stati aggiunti ad un ordine');
                });
            }
        }
    });

    // Add action client to registry
    core.action_registry.add("netaddiction_purchase_orders.product_list", ProductList);

    return {
        ProductList: ProductList,
        List: List,
    }
});
