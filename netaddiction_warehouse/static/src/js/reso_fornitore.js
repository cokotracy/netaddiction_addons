// TODO the action client reso fornitore has been removed
// odoo.define('netaddiction_warehouse.supplier_reverse', function (require) {
//     "use strict";

//     var core = require('web.core');
//     var session = require('web.session');
//     var Widget = require('web.Widget');
//     var Dialog = require('web.Dialog');
//     var ActionManager = require('web.ActionManager');

//     var _t = core._t;
//     var qweb = core.qweb;

//     // New requirements
//     var AbstractAction = require('web.AbstractAction');

//     /**
//      * ClientAction declaration add into registry at the end
//      */
//     var reverse = AbstractAction.extend({
//         init: function (parent, action, options) {
//             console.log("Reverse AbstractAction");
//             this._super.apply(this, arguments);
//             this.action = action;
//             this.parent = parent;
//             this.dialog;
//         },
//         start: function () {
//             this._super.apply(this, arguments);
//             var self = this;
//             this._rpc({
//                 model: 'res.partner',
//                 method: 'search_read',
//                 fields: [
//                     'id',
//                     'name'
//                 ],
//                 domain: [
//                     ['supplier','=',true],
//                     ['active', '=', true],
//                     ['parent_id', '=', false],
//                     ['company_id', '=', parseInt(session.company_id)]
//                 ],
//             }).then(function (suppliers) {
//                 var options = {
//                     title: "Reso a Fornitore - ",
//                     subtitle: 'Scegli il Fornitore',
//                     size: 'large',
//                     dialogClass: '',
//                     $content: qweb.render(
//                         'dialog_content_supplier_reverse',
//                         {suppliers: suppliers}
//                     ),
//                     buttons: [
//                         {
//                             text: _t("Chiudi"),
//                             close: true,
//                             classes: "btn-primary"
//                         },
//                         {
//                             text: "Avanti",
//                             classes: "btn-success",
//                             click: function () {
//                                 return self.goNext();
//                             },
//                         }
//                     ]
//                 }
//                 self.dialog = new Dialog(this, options);
//                 self.dialog.open();
//             });
//         },
//         goNext: function (e) {
//             var sup_id = $('#select_supplier_reverse').val();
//             var name = $('#select_supplier_reverse :selected').text();
//             var supplier = {
//                 'id': sup_id,
//                 'name': name
//             }
//             var supplier_reverse = new page_supplier_reverse(this, supplier);
//             this.$el.html('');
//             supplier_reverse.appendTo(this.$el);
//             this.dialog.close();
//         }
//     });

//     /**
//      * page_supplier_reverse Widget
//      */
//     var page_supplier_reverse = Widget.extend({
//         template: 'page_supplier_reverse',
//         events: {
//             'click .change_reverse_pick': 'doChangeListReverse',
//             'click .o_pager_next': 'doPager',
//             'click .o_pager_previous': 'doPager',
//             'click .open_product': 'doOpenProduct',
//             'change #search_supplier': 'FilterSupplier',
//             'change #search': 'SearchProduct',
//             'click .reverse_select_all': 'SelectAll',
//             'click .product_selector': 'SelectSingle',
//             'click #send_reverse': 'Reverse'
//         },
//         init: function (parent, supplier) {
//             this._super(parent);
//             this.supplier = supplier;
//             this.operations = {};
//             this.products = {};
//             this.pager = null;
//             this.limit = 40;
//             this.total_mag = 0;
//             this.actionmanager = new ActionManager(this);
//             this.selectedProducts = {
//                 'scraped': new Array(),
//                 'commercial': new Array()
//             };
//             var self = this;

//             this._rpc({
//                 model: 'netaddiction.warehouse.operations.settings',
//                 method: 'search_read',
//                 fields: [],
//                 domain: [
//                     ['company_id', '=', session.company_id]
//                 ],
//             }).then(function (configs) {
//                 var ids_conf = []
//                 var config_conf = []
//                 for (var i in configs) {
//                     self.operations[configs[i].netaddiction_op_type] = {}
//                     self.operations[configs[i].netaddiction_op_type]['operation_type_id'] = configs[i].operation[0];
//                     ids_conf.push(parseInt(configs[i].operation[0]));
//                     config_conf.push(configs[i].netaddiction_op_type);
//                 }

//                 self._rpc({
//                     model: 'stock.picking.type',
//                     method: 'search_read',
//                     fields: [
//                         'default_location_src_id',
//                         'default_location_dest_id',
//                     ],
//                     domain: [
//                         ['id', 'in', ids_conf]
//                     ],
//                 }).then(function (res) {
//                     // Prepare operations
//                     for (let r in res) {
//                         self.operations[config_conf[r]]['default_location_src_id'] = res[r].default_location_src_id
//                         self.operations[config_conf[r]]['default_location_dest_id'] = res[r].default_location_dest_id
//                     }

//                     self._rpc({
//                         model: 'res.partner',
//                         method: 'search_read',
//                         fields: [
//                             'id',
//                             'name'
//                         ],
//                         domain: [
//                             ['supplier','=',true],
//                             ['active', '=', true],
//                             ['parent_id', '=', false],
//                         ],
//                     }).then(function (suppliers) {
//                         var html = '';
//                         for (var sup in suppliers) {
//                             var selected = '';
//                             if (parseInt(suppliers[sup].id) === parseInt(self.supplier.id)) {
//                                 selected = ' selected="selected" ';
//                             }
//                             html = html + "<option value='" + suppliers[sup].id + "' " + selected + ">" + suppliers[sup].name + "</option>";
//                         }
//                         $('#search_supplier').append(html);
//                         self.get_scraped_products(self.supplier.id, 1, null);
//                     });

//                 });
//             });
//         },
//         /**
//          *
//          * @param e
//          * @returns {*}
//          * @constructor
//          */
//         Reverse: function (e) {
//             var self = this;
//             var scrap = this.selectedProducts.scraped.length
//             var comm = this.selectedProducts.commercial.length
//             if (scrap == 0 && comm == 0) {
//                 let title = 'ERRORE';
//                 let text = 'Devi mettere nella lista reso almeno un prodotto';
//                 return self.do_warn(title, text);
//             }

//             this._rpc({
//                 model: 'stock.picking',
//                 method: 'create_supplier_reverse',
//                 args: [
//                     JSON.stringify(self.selectedProducts),
//                     self.supplier.id,
//                     JSON.stringify(self.operations)
//                 ],
//             }).then(function (res) {
//                 let title = 'RESO EFFETTUATO';
//                 let text = 'Ho creato la lista di prelievo per i prodotti selezionati';
//                 return self.do_warn(title, text);
//             });
//         },
//         /**
//          *
//          * @param e
//          * @constructor
//          */
//         FilterSupplier: function (e) {
//             var sid = $(e.currentTarget).val();
//             var name = $(e.currentTarget).find(':selected').text();
//             var supplier = {
//                 'id': sid,
//                 'name': name
//             }
//             // Create a new instance of page_supplier_revers with current widget parent
//             var supplier_reverse = new page_supplier_reverse(this.getParent(), supplier);
//             this.destroy();
//             // Append the new instance to the destroyed widget's parent
//             supplier_reverse.appendTo(supplier_reverse.getParent().$el);
//         },
//         /**
//          *
//          * @param e
//          * @constructor
//          */
//         SearchProduct: function (e) {
//             var name = $(e.currentTarget).val();
//             this.get_wh_products(this.supplier.id, 1, name)
//         },
//         /**
//          *
//          * @param e
//          */
//         doChangeListReverse: function (e) {
//             $('.change_reverse_pick').removeClass('active_reverse');
//             $(e.currentTarget).addClass('active_reverse');
//             var id = $(e.currentTarget).attr('id');

//             this.get_product_list(id);
//         },
//         /**
//          *
//          * @param wharehouse
//          */
//         get_product_list: function (wharehouse) {
//             var name = null;
//             var searched = $('#search').val();
//             if (searched != ' ') {
//                 name = searched;
//             }
//             if (wharehouse == 'scrapped_wh_link') {
//                 this.get_scraped_products(this.supplier.id, name);
//             } else {
//                 this.get_wh_products(this.supplier.id, name);
//             }
//         },
//         /**
//          *
//          * @param supplier_id
//          * @param product_name
//          */
//         get_wh_products: function (supplier_id, product_name) {
//             var self = this;
//             $('#purchase_in_product_list').remove();
//             $('#pager').html('');
//             this.products = {};
//             var location_id = this.operations.reverse_supplier.default_location_src_id[0];
//             var filter = [['company_id', '=', session.company_id], ['location_id', '=', parseInt(location_id)]]
//             if (product_name != null) {
//                 var filter = [['company_id', '=', session.company_id], ['location_id', '=', parseInt(location_id)], ['product_id.name', 'ilike', product_name]]
//             }

//             this._rpc({
//                 model: 'product.product',
//                 method: 'get_product_from_supplier',
//                 args: [
//                     supplier_id,
//                 ],
//             }).then(function (result) {
//                 var count = 0
//                 self.total_mag = 0;
//                 for (var p in result) {
//                     self.products[result[p].id] = {}
//                     self.products[result[p].id]['id'] = result[p].id
//                     self.products[result[p].id]['name'] = result[p].name
//                     self.products[result[p].id]['qty'] = result[p].qty
//                     self.products[result[p].id]['inventory_value'] = result[p].inventory_value.toLocaleString()
//                     self.products[result[p].id]['single_inventory'] = result[p].single_inventory.toLocaleString()
//                     self.total_mag = self.total_mag + result[p].inventory_value
//                     count = count + 1
//                 }
//                 self.total_mag = self.total_mag.toLocaleString();
//                 $('#total_mag').remove();
//                 $('#search_supplier').after('<span id="total_mag" class="ml-1">&nbsp;<span>Totale Magazzino: </span><b>' + self.total_mag + '</b></span>');

//                 $('#content_reverse').html(qweb.render('table_scraped', {products: self.products}));

//                 $(self.selectedProducts.commercial).each(function (index, product) {
//                     $('#qta_' + product.pid).val(product.qta)
//                     $('#sel_' + product.pid).prop('checked', true)
//                 });
//             });
//         },
//         /**
//          *
//          * @param supplier_id
//          * @param product_name
//          */
//         get_scraped_products: function (supplier_id, product_name) {
//             var self = this;
//             $('.product_line').remove();
//             $('#pager').html('');
//             self.total_mag = 0;
//             this.products = {};
//             var location_id = this.operations.reverse_supplier_scraped.default_location_src_id[0];
//             var filter = [['company_id', '=', session.company_id], ['location_id', '=', parseInt(location_id)]]
//             if (product_name != null) {
//                 var filter = [['company_id', '=', session.company_id], ['location_id', '=', parseInt(location_id)], ['product_id.name', 'ilike', product_name]]
//             }

//             this._rpc({
//                 model: 'product.product',
//                 method: 'get_scraped_product_from_supplier',
//                 args: [
//                     supplier_id,
//                 ],
//             }).then(function (result) {
//                 let count = 0
//                 for (let p in result) {
//                     self.products[result[p].id] = {}
//                     self.products[result[p].id]['id'] = result[p].id
//                     self.products[result[p].id]['name'] = result[p].name
//                     self.products[result[p].id]['qty'] = result[p].qty
//                     self.products[result[p].id]['inventory_value'] = result[p].inventory_value.toLocaleString()
//                     self.products[result[p].id]['single_inventory'] = result[p].single_inventory.toLocaleString()
//                     self.total_mag = self.total_mag + result[p].inventory_value
//                     count = count + 1
//                 }
//                 self.total_mag = self.total_mag.toLocaleString();
//                 $('#total_mag').remove();
//                 $('#search_supplier').after('<span id="total_mag" class="ml-1">&nbsp;<span>Totale Magazzino: </span><b>' + self.total_mag + '</b></span>');
//                 $('#content_reverse').html(qweb.render('table_scraped', {products: self.products}));

//                 $(self.selectedProducts.scraped).each(function (index, product) {
//                     $('#qta_' + product.pid).val(product.qta)
//                     $('#sel_' + product.pid).prop('checked', true)
//                 });
//             });
//         },
//         /**
//          *
//          * @param e
//          */
//         doPager: function (e) {
//             var id = $('.active_reverse').attr('id');
//             if (id == 'scrapped_wh_link') {
//                 this.get_scraped_products(this.supplier.id, this.pager.state.current_min, null);
//             } else {
//                 this.get_wh_products(this.supplier.id, this.pager.state.current_min, null);
//             }

//         },
//         /**
//          *
//          * @param e
//          */
//         doOpenProduct: function (e) {
//             e.preventDefault();
//             var id = $(e.currentTarget).closest('tr').attr('data-id')
//             this.actionmanager.do_action({
//                 type: 'ir.actions.act_window',
//                 res_model: "product.product",
//                 res_id: parseInt(id),
//                 views: [[false, 'form']],
//                 target: 'new',
//                 context: {},
//                 flags: {'form': {'action_buttons': true}}
//             });
//         },
//         /**
//          *
//          * @param e
//          * @constructor
//          */
//         SelectAll: function (e) {
//             var self = this;
//             var checked = $(e.currentTarget).is(':checked');
//             if (checked) {
//                 $('.product_selector').prop('checked', true);
//                 $('.product_selector').each(function (index, value) {
//                     var pid = $(value).closest('.product_line').attr('data-id')
//                     var qta = $(value).closest('.product_line').find('.qty_reverse').val();
//                     self.selected_product(pid, qta, 'add');
//                 })
//             } else {
//                 $('.product_selector').prop('checked', false);
//                 $('.product_selector').each(function (index, value) {
//                     var pid = $(value).closest('.product_line').attr('data-id')
//                     var qta = $(value).closest('.product_line').find('.qty_reverse').val();
//                     self.selected_product(pid, qta, 'remove');
//                 })
//             }
//         },
//         /**
//          *
//          * @param e
//          * @constructor
//          */
//         SelectSingle: function (e) {
//             var self = this;
//             var pid = $(e.currentTarget).closest('.product_line').attr('data-id');
//             var qta = $(e.currentTarget).closest('.product_line').find('.qty_reverse').val();
//             var checked = $(e.currentTarget).is(':checked');
//             if (checked) {
//                 this.selected_product(pid, qta, 'add')
//             } else {
//                 this.selected_product(pid, qta, 'remove')
//             }
//         },
//         /**
//          *
//          * @param pid
//          * @param qta
//          * @param action
//          * @returns {*}
//          */
//         selected_product: function (pid, qta, action) {
//             var self = this;
//             if (parseInt(qta) == 0 && action == 'add') {
//                 var name = $('#product_' + pid).text()
//                 let title = 'ERRORE';
//                 let text = 'La quantità del prodotto <b>' + name + '</b> non può essere 0';
//                 $('#product_' + pid).closest('.product_line').find('.product_selector').prop('checked', false);
//                 return self.do_warn(title, text);

//             }
//             var id = $('.active_reverse').attr('id');
//             var attr = {
//                 'pid': pid,
//                 'qta': qta
//             }
//             if (id == 'scrapped_wh_link') {
//                 if (action == 'add') {
//                     this.selectedProducts.scraped.push(attr)
//                 } else {
//                     var i = this.selectedProducts.scraped.map(function (e) {
//                         return e.pid;
//                     }).indexOf(pid);
//                     if (i != -1) {
//                         this.selectedProducts.scraped.splice(i, 1);
//                     }
//                 }
//             } else {
//                 if (action == 'add') {
//                     this.selectedProducts.commercial.push(attr)
//                 } else {
//                     var i = this.selectedProducts.commercial.map(function (e) {
//                         return e.pid;
//                     }).indexOf(pid);
//                     if (i != -1) {
//                         this.selectedProducts.commercial.splice(i, 1);
//                     }
//                 }
//             }
//         }
//     });

//     // Add to action_registry the reverse ClientAction Widget
//     core.action_registry.add("netaddiction_warehouse.supplier_reverse", reverse);
// })
