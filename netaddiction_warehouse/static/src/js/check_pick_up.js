odoo.define('netaddiction_warehouse.check_pick_up', function (require) {
    "use strict";

    var core = require('web.core');
    var session = require('web.session');
    var Widget = require('web.Widget');
    var _t = core._t;
    var Qweb = core.qweb;

    // New requirements
    var AbstractAction = require('web.AbstractAction');
    var Dialog = require('web.Dialog');

    var url_report = '/report/pdf/netaddiction_warehouse.bolla_di_spedizione/';

    function wash_and_focus_input(element) {
        $(element).val('');
        $(element).focus();
    }

    function color_tr(tr) {
        $(tr).css('background', '#449d44');
        $(tr).find('a').css('color', 'white');
        $(tr).css('color', 'white');
    }

    function return_color_tr(tr, back_color) {
        $(tr).css('background', back_color);
        $(tr).find('a').css('color', '#337ab7');
        $(tr).css('color', '#4c4c4c');
    }

    function disable_tr(tr) {
        $(tr).css('color', '#dddddd');
        $(tr).find('a').css('color', '#dddddd');
        $(tr).addClass('finished');
    }

    function show_complete() {
        var count_finished = 0;
        var count_all = 0;
        $('.order_product_list').each(function (index, value) {
            count_all = count_all + 1;
            if ($(value).hasClass('finished')) {
                count_finished = count_finished + 1;
            }
        });

        if (count_finished == count_all) {
            $('#validate_order').show();
        }
    }

    var controllo_pickup = AbstractAction.extend({
        init: function (parent, action, options) {
            this._super.apply(this, arguments);
            this.action = action;
            this.action_manager = parent;
        },
        start: function () {
            this._super.apply(this, arguments);
            var self = this;
            return this._rpc({
                model: 'stock.picking.batch',
                method: 'search_read',
                fields: [
                    'display_name',
                    'id',
                    'picking_ids'
                ],
                domain: [
                    ['state', '=', 'in_progress'],
                    ['in_exit', '=', false],
                    ['reverse_supplier', '=', false]
                ],
            }).then(function (filtered) {
                self._rpc({
                    model: 'stock.picking.batch',
                    method: 'search_read',
                    fields: [
                        'display_name',
                        'id',
                        'picking_ids'
                    ],
                    domain: [
                        ['picking_ids.sale_id.is_b2b', '=', true],
                        ['state', '=', 'in_progress'],
                        ['in_exit', '=', false],
                        ['reverse_supplier', '=', false]
                    ],
                }).then(function (b2b) {
                    $.each(filtered, function (i, v) {
                        $.each(b2b, function (k, b) {
                            if (b.id === v.id) {
                                v.is_b2b = true;
                            }
                        })
                    });
                    let list = new homepage(self, filtered);
                    // TODO i don't now why but self.$el is the o_action div
                    //  that contain an o_content div yet. For now we just
                    //  clear the o_action div and put new widget inside it
                    self.$el.html('');
                    list.appendTo(self.$el);
                });
            });
        },
    });

    var homepage = Widget.extend({
        template: 'control_pick_up_homepage',
        events: {
            "click .batch_tr": "doOpenWave",
        },
        init: function (parent, batchs) {
            this._super(parent);
            this.batchs = batchs;
            this.parent = parent;
            var home = this;
        },
        doOpenWave: function (e) {
            var home = this;
            var id = $(e.currentTarget).attr('data-id');
            var batch_name = $(e.currentTarget).find('.batch_name').text();
            var b2b = $(e.currentTarget).attr('data-b2b');
            if (b2b) {
                var open = new OpenB2B(home, id, batch_name);
            } else {
                var open = new openList(home, id, batch_name);
            }
            home.do_hide();
            open.appendTo(home.parent.$el)
        }
    });

    var OpenB2B = Widget.extend({
        template: 'open_batch_b2b',
        events: {
            "change #search": "doSearchBarcode",
            "click #complete_b2b": "doCloseB2B",
            "click #control_homepage": "doReturnParent",
        },
        init: function (parent, batch_id, batch_name) {
            this._super(parent);
            this.batch_id = batch_id;
            this.batch_name = batch_name;
            this.results = {};
            $('#search').val('');
            $('#search').focus();
            this._rpc({
                model: 'stock.move.line',
                method: 'search_read',
                fields: [
                    'product_id',
                    'qty_done'
                ],
                domain: [
                    ['picking_id.batch_id', '=', parseInt(batch_id)]
                ],
            }).then(function (results) {
                var all_results = {};
                $.each(results, function (i, v) {
                    if (v.product_id[0] in all_results) {
                        all_results[v.product_id[0]]['qty_done'] = all_results[v.product_id[0]]['qty_done'] + v.qty_done;
                    } else {
                        all_results[v.product_id[0]] = {};
                        all_results[v.product_id[0]]['qty_done'] = v.qty_done;
                        all_results[v.product_id[0]]['product'] = v.product_id;
                    }
                });
                $('.open_batch_list').append(Qweb.render('b2b_list', {results: all_results}));
            });
        },
        doReturnParent: function (e) {
            var self = this;
            e.preventDefault();
            self.getParent().do_show();
            self.destroy();
            $('#search').val('');
            $('#search').focus();
        },
        doCloseB2B: function (e) {
            var self = this;
            this._rpc({
                model: 'stock.picking.batch',
                method: 'close_b2b_batch',
                args: [
                    this.batch_id,
                    this.batch_id
                ],
            }).then(function (res) {
                // TODO change report with a simple DDT from module l10n_it_ddt
                /*let data = {
                    'ids': [res['invoice']],
                    'model': 'account.invoice',
                };
                self.do_action({
                    type: 'ir.actions.report',
                    report_name: 'netaddiction_b2b.bolla_di_spedizione_b2b',
                    datas: data,

                });*/
            });
        },
        doSearchBarcode: function (e) {
            var self = this;
            e.preventDefault();
            var barcode_list = [];
            var barcode = $(e.currentTarget).val();
            barcode_list.push(barcode);

            barcode = '0' + barcode;
            barcode_list.push(barcode);

            barcode = barcode.replace(/^0+/, '');
            barcode_list.push(barcode);

            barcode = barcode.toLowerCase();
            barcode_list.push(barcode);
            barcode = barcode.charAt(0).toUpperCase() + barcode.slice(1);
            barcode_list.push(barcode);

            barcode = barcode.toUpperCase();
            barcode_list.push(barcode);
            wash_and_focus_input($('#search'));
            this._rpc({
                model: 'product.product',
                method: 'search_read',
                domain: [
                    ['barcode', 'in', barcode_list]
                ],
                limit: 1,
            }).then(function (product) {
                if (!product || product.length === 0) {
                    return self.do_warn('BARCODE INESISTENTE');
                } else {
                    var go = false;
                    $.each($(self.$el).find('.row_product'), function (i, v) {
                        var id = $(v).attr('data-id');
                        if (parseInt(id) == parseInt(product[0].id)) {
                            self.get_product(v);
                            go = true;
                        }
                    });
                    if (!go) {
                        return self.do_warn('BARCODE NON PRESENTE IN LISTA');
                    }
                }
            });
        },
        get_product: function (row) {
            var qty_done = parseInt($(row).find('.qty_done').text());
            var back_color = $(row).css('background');
            if (qty_done > 0) {
                color_tr($(row));

                setTimeout(function () {
                    return_color_tr($(row), back_color);
                }, 400);

                $(row).find('.qty_done').text((qty_done - 1));
                if ((qty_done - 1) == 0) {
                    $(row).find('td').css('color', '#dddddd');
                    $(row).addClass('finished');
                }
                var st = true;

                var count_all = 0;
                var count_finished = 0;
                $(row).closest('tr').each(function (index, value) {
                    count_all = count_all + 1;
                    if ($(value).hasClass('finished')) {
                        count_finished = count_finished + 1;
                    }
                });

                if (count_finished == count_all) {
                    $('#complete_b2b').show();
                }
            }
        }
    });

    var openList = Widget.extend({
        template: 'open_batch',
        events: {
            "click #control_homepage": "doReturnParent",
            "change #search": "doSearchBarcode",
            "click .sale_order": "doOpenOrder",
            "click .picking_order": "doOpenPick",
            "click .partner": "doOpenPartner",
            "click .choose": "doGoToOrder",
            "click .complete": "ValidateOrderTr",
            "click #validateAll": "ValidateOrderAll",
            'change .explode_barcode': "SearchProduct",
            'click .open_under': 'OpenUnder'
        },
        init: function (parent, batch_id, batch_name) {
            this._super(parent);
            this.batch_id = batch_id;
            this.batch_name = batch_name;
            var this_list = this;
            $('#search').val('');
            $('#search').focus();
            //get_products_residual(batch_id)
        },
        doReturnParent: function (e) {
            var home = this;
            e.preventDefault();
            home.getParent().do_show();
            home.destroy();
            $('#search').val('');
            $('#search').focus();
        },
        doSearchBarcode: function (e) {
            e.preventDefault();
            var self = this;
            var barcode_list = [];
            var barcode = $(e.currentTarget).val();
            barcode_list.push(barcode);

            barcode = '0' + barcode;
            barcode_list.push(barcode);

            barcode = barcode.replace(/^0+/, '');
            barcode_list.push(barcode);

            barcode = barcode.toLowerCase();
            barcode_list.push(barcode);
            barcode = barcode.charAt(0).toUpperCase() + barcode.slice(1);
            barcode_list.push(barcode);

            barcode = barcode.toUpperCase();
            barcode_list.push(barcode);
            $('.open_batch_list').children().remove();

            this._rpc({
                model: 'stock.picking',
                method: 'search_read',
                fields: ['id', 'batch_id', 'move_line_ids', 'display_name', 'sale_id', 'partner_id'],
                domain: [
                    ['move_line_ids.product_id.barcode', 'in', barcode_list],
                    ['batch_id', '=', parseInt(self.batch_id)],
                    ['state', 'not in', ['draft', 'cancel', 'done']]
                ],
            }).then(function (filtered) {
                if (filtered.length == 0) {
                    $('.picking_list').remove();
                    self.do_warn('BARCONE INESISTENTE', 'Il barcode  non è presente nella lista');
                    wash_and_focus_input(e.currentTarget);
                } else {
                    var ids = [];
                    var count_products = {};
                    var count_all = {};
                    var products_array = {};
                    for (var key in filtered) {
                        products_array[filtered[key].id] = {}
                        for (var i in filtered[key].move_line_ids) {
                            ids.push(filtered[key].move_line_ids[i]);
                            count_products[filtered[key].id] = 0;
                            count_all[filtered[key].id] = 0;
                        }
                    }
                    self._rpc({
                        model: 'stock.move.line',
                        method: 'search_read',
                        fields: ['qty_done', 'product_id', 'picking_id', 'product_qty'],
                        domain: [['id', 'in', ids]],
                    }).then(function (result) {
                        for (var k in result) {
                            var inte = parseInt(result[k].picking_id[0]);
                            count_products[inte] = count_products[inte] + parseInt(result[k].qty_done);
                            count_all[inte] = count_all[inte] + parseInt(result[k].product_qty);
                            var arr = new Array();
                            arr['product_id'] = result[k].product_id;
                            arr['qty'] = result[k].product_qty;
                            products_array[inte][result[k].product_id[0]] = arr;
                        }
                        $('.open_batch_list').append(Qweb.render('open_batch_order_list', {
                            'orders': filtered,
                            'count_products': count_products,
                            'count_all': count_all,
                            'explodes': products_array
                        }));
                        $('#validateAll').show();
                    });
                }
            });
        },
        OpenUnder: function (e) {
            var wid = $(e.currentTarget).closest('tr').attr('data-id');
            $(e.currentTarget).hide();
            $('#under_tr_' + wid).show();
            $('#under_tr_' + wid).find('.explode_barcode').focus();
        },
        SearchProduct: function (e) {
            var self = this;
            var barcode_list = [];
            var barcode = $(e.currentTarget).val();
            barcode_list.push(barcode);

            barcode = '0' + barcode;
            barcode_list.push(barcode);

            barcode = barcode.replace(/^0+/, '');
            barcode_list.push(barcode);

            barcode = barcode.toLowerCase();
            barcode_list.push(barcode);
            barcode = barcode.charAt(0).toUpperCase() + barcode.slice(1);
            barcode_list.push(barcode);

            barcode = barcode.toUpperCase();
            barcode_list.push(barcode);
            this._rpc({
                model: 'product.product',
                method: 'search_read',
                fields: ['id'],
                domain: [['barcode', 'in', barcode_list]],
                limit: 1,
            }).then(function (pid) {
                wash_and_focus_input($('.explode_barcode'));
                var st = false;
                if (pid != null && pid.length !== 0) {
                    var wid = $(e.currentTarget).attr('data-id');
                    $('#table_' + wid + ' tr').each(function (inv, vl) {
                        if (parseInt($(vl).attr('data-id')) == parseInt(pid[0].id)) {
                            var qty_done = parseInt($(vl).find('.qty_done').text());
                            var back_color = $(vl).css('background');
                            if (qty_done > 0) {
                                color_tr($('#table_' + wid + ' .pid_' + pid[0].id));

                                setTimeout(function () {
                                    return_color_tr($(vl), back_color);
                                }, 400);

                                $(vl).find('.qty_done').text((qty_done - 1))
                                if ((qty_done - 1) == 0) {
                                    $(vl).find('td').css('color', '#dddddd');
                                    $(vl).addClass('finished');
                                }
                                st = true;

                                var count_all = 0;
                                var count_finished = 0;
                                $('#table_' + wid + ' tr').each(function (index, value) {
                                    count_all = count_all + 1;
                                    if ($(value).hasClass('finished')) {
                                        count_finished = count_finished + 1;
                                    }
                                });

                                if (count_finished == count_all) {
                                    $('#complete_' + wid).show();
                                }
                            } else {
                                st = true;
                                return self.do_warn('PRODOTTO GIA TERMINATO', 'Il barcode <b>' + barcode + '</b> appartiene ad un prodotto già terminato');
                            }
                        }
                    })
                } else {
                    st = true
                    return self.do_warn('BARCODE INESISTENTE', 'Il barcode <b>' + barcode + '</b> non esiste');
                }

                if (!st) {
                    return self.do_warn('BARCODE NON PRESENTE', 'Il barcode <b>' + barcode + '</b> non è presente nell\'ordine corrente');
                }
            });
        },
        doOpenOrder: function (e) {
            e.preventDefault();
            var id = $(e.currentTarget).attr('data-id');
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "sale.order",
                res_id: parseInt(id),
                views: [[false, 'form']],
                target: 'new',
                context: {},
            });
        },
        doOpenPick: function (e) {
            e.preventDefault();
            var id = $(e.currentTarget).attr('data-id');
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "stock.picking",
                res_id: parseInt(id),
                views: [[false, 'form']],
                target: 'new',
                context: {},
            });
        },
        doOpenPartner: function (e) {
            e.preventDefault();
            var id = $(e.currentTarget).attr('data-id');
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "res.partner",
                res_id: parseInt(id),
                views: [[false, 'form']],
                target: 'new',
                context: {},
            });
        },
        // FIXME: This onclick handler seems to be useless, i don't find any element with class choose
        doGoToOrder: function (e) {
            e.preventDefault();
            var self = this;
            var id = $(e.currentTarget).closest('tr').attr('data-id');
            var picking_order = $(e.currentTarget).closest('tr').find('.picking_order').text();
            var sale_order = $(e.currentTarget).closest('tr').find('.sale_order').text();
            var order_name = sale_order + ' | ' + picking_order;
            this._rpc({
                model: 'stock.move.line',
                method: 'search_read',
                fields: ['qty_done', 'product_id', 'picking_id'],
                domain: [['picking_id', '=', parseInt(id)]],
            }).then(function (result) {
                var new_order = new singleOrder(self, id, self.batch_name, order_name, result);
                self.do_hide();
                new_order.appendTo(home.parent.$el);
            });
        },
        ValidateOrderTr: function (e) {
            var id = $(e.currentTarget).closest('tr').attr('data-id');
            var url = url_report + id;
            var pop = window.open(url, 'titolo', 'scrollbars=no,resizable=yes, width=1000,height=700,status=no,location=no,toolbar=no');
            pop.print();
            this._rpc({
                model: 'stock.picking',
                method: 'do_validate_orders',
                args: [id],
            }).then(function (result) {
                let value;
                if (result) {
                    pop.close();
                    value = $(e.currentTarget).closest('tr');
                    $(value).css('color', 'red');
                    $(value).find('a').css('color', 'red');
                    $(value).find('button').hide();
                    $('#under_tr_' + id).hide();
                    $('#search').val('');
                    $('#search').focus();
                    return this_list.do_warn('ORDINE NON IN LAVORAZIONE', result['error']);
                }
                value = $(e.currentTarget).closest('tr');
                $(value).css('color', '#dddddd');
                $(value).find('a').css('color', '#dddddd');
                $(value).find('button').hide();
                $('#under_tr_' + id).hide();
                $('#search').val('');
                $('#search').focus();
            });
        },
        ValidateOrderAll: function (e) {
            var self = this;
            var trs = [];
            $('.nprod').each(function (index, value) {
                if (parseInt($(value).text()) == 1) {
                    trs.push(parseInt($(value).closest('tr').attr('data-id')));
                    disable_tr($(value).closest('tr'));
                    $(value).closest('tr').find('.complete').hide();
                }
            })
            this._rpc({
                model: 'stock.picking',
                method: 'do_multi_validate_orders',
                args: [trs],
            }).then(function (result) {
                if (result) {
                    $('.order_tr').each(function (index, value) {
                        var i = parseInt($(value).attr('data-id'));
                        $.each(result['error'], function (z, b) {
                            if (parseInt(b) == i) {
                                $(value).css('color', 'red');
                                $(value).find('a').css('color', 'red');
                                $(value).find('button').hide();
                            }
                        });
                        let data = {
                            'ids': result['print'],
                            'model': 'stock.picking',
                        };
                        let action = {
                            type: 'ir.actions.report',
                            report_type: 'qweb-pdf',
                            report_name: 'netaddiction_warehouse.bolla_di_spedizione',
                            data: data,
                        };
                        self.do_action(action);
                    })
                } else {
                    let data = {
                        'ids': trs,
                        'model': 'stock.picking',
                    }
                    let action = {
                        type: 'ir.actions.report',
                        report_type: 'qweb-pdf',
                        report_name: 'netaddiction_warehouse.bolla_di_spedizione',
                        data: data,
                    };
                    self.do_action(action);
                }

                $('#search').val('');
                $('#search').focus();
            });
        }
    });

    // FIXME Check if this widget is needed or not, the only method that instantiate this widget it's doGoToOrder
    //  from widget openList but there isn't any trigger inside the related template view.
    //  If we need this widget it must be tested because the this_* reference are incorrect
    var singleOrder = Widget.extend({
        template: 'single_order',
        events: {
            "click #control_batch": "returnWave",
            "click #control_homepage": "returnHome",
            "click .product": "GoToProduct",
            "change #search_in_order": "SearchProduct",
            "click #gotoSped": "GoToPicking",
            "click #validate_order": "ValidateOrder",

        },
        init: function (parent, id, batch_name, order_name, products) {
            this._super(parent);
            this.order_id = id;
            this.batch_name = batch_name;
            this.order_name = order_name;
            this.products = products;
            var this_order = this;
        },
        returnWave: function (e) {
            e.preventDefault();
            this_list.do_show();
            this_order.destroy();
        },
        returnHome: function (e) {
            e.preventDefault();
            home.do_show();
            this_list.destroy();
            this_order.destroy();
        },
        GoToProduct: function (e) {
            e.preventDefault();
            var id = $(e.currentTarget).attr('data-id');
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "product.product",
                res_id: parseInt(id),
                views: [[false, 'form']],
                target: 'new',
                context: {},
            });
        },
        GoToPicking: function (e) {
            e.preventDefault();
            var id = $(e.currentTarget).attr('data-id');
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: "stock.picking",
                res_id: parseInt(id),
                views: [[false, 'form']],
                target: 'new',
                context: {},
            });
        },
        SearchProduct: function (e) {
            var barcode_list = []
            var barcode = $(e.currentTarget).val();
            barcode_list.push(barcode)

            barcode = '0' + barcode
            barcode_list.push(barcode)

            barcode = barcode.replace(/^0+/, '');
            barcode_list.push(barcode)

            barcode = barcode.toLowerCase();
            barcode_list.push(barcode)
            barcode = barcode.charAt(0).toUpperCase() + barcode.slice(1);
            barcode_list.push(barcode)

            barcode = barcode.toUpperCase();
            barcode_list.push(barcode)
            this._rpc({
                model: 'product.product',
                method: 'search_read',
                fields: ['id'],
                domain: [['barcode', 'in', barcode_list]],
                limit: 1,
            }).then(function (pid) {
                if (pid != null && pid.length > 0) {
                    for (var p in this_order.products) {
                        if (this_order.products[p].product_id[0] == pid[0].id) {
                            var qty_done = parseInt($('.pid_' + pid[0].id).find('.qty_done').text());
                            if (qty_done > 0) {
                                var back_color = $('.pid_' + pid[0].id).css('background');
                                color_tr($('.pid_' + pid[0].id));
                                return setTimeout(function () {
                                    return_color_tr($('.pid_' + pid[0].id), back_color);
                                    wash_and_focus_input($('#search_in_order'));
                                    $('.pid_' + pid[0].id).find('.qty_done').text((qty_done - 1));
                                    if ((qty_done - 1) == 0) {
                                        disable_tr($('.pid_' + pid[0].id));
                                    }

                                    show_complete();

                                }, 1100);
                            } else {
                                return this_order.do_warn('PRODOTTO GIA TERMINATO', 'Il barcode <b>' + barcode + '</b> appartiene ad un prodotto già terminato');
                            }
                        }
                    }
                } else {
                    return this_order.do_warn('BARCODE INESISTENTE', 'Il barcode <b>' + barcode + '</b> non esiste');
                }

                return this_order.do_warn('BARCODE NON PRESENTE', 'Il barcode <b>' + barcode + '</b> non è presente nell\'ordine corrente');
            });
        },
        ValidateOrder: function (e) {
            var url = url_report + this_order.order_id
            var pop = window.open(url, 'titolo', 'scrollbars=no,resizable=yes, width=1000,height=700,status=no,location=no,toolbar=no');
            pop.print()
            this._rcp({
                model: 'stock.picking',
                method: 'do_validate_orders',
                args: [this_order.order_id],
            }).then(function (result) {
                $('.order_tr').each(function (index, value) {
                    if ($(value).attr('data-id') == this_order.order_id) {
                        $(value).css('color', '#dddddd');
                        $(value).find('a').css('color', '#dddddd');
                        $(value).find('button').hide();
                        this_order.destroy();
                        this_list.do_show();
                    }
                })
                $('#search').val('');
                $('#search').focus();
            });
        },

    });

    // Add to action_registry the reverse ClientAction Widget
    core.action_registry.add('netaddiction_warehouse.controllo_pickup', controllo_pickup);
});
