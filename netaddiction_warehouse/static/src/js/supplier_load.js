odoo.define('netaddiction_warehouse.supplier_load', function (require) {
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

    function count_products(this_cgo) {
        var number_tot = 0;
        var number_prod = 0;
        for (let i in this_cgo.products) {
            number_prod = number_prod + 1;
            number_tot = number_tot + parseInt(this_cgo.products[i])
        }
        $('#number_tot').text(number_tot);
        $('#number_prod').text(number_prod);
    }

    function list_products(this_cgo) {
        for (let p in this_cgo.products) {
            var tr = '<tr><td class="qty_ordered">' + this_cgo.products_ordered[p] + '</td><td class="qty">' + this_cgo.products[p] + '</td><td class="pname">' + p + '</td><td class="price_' + this_cgo.pid[p] + '"></tr></tr>';
            $('#purchase_in_product_list tbody').append(tr);
        }
        get_price(this_cgo)
    }

    function get_price(widget) {
        var pids = widget.pid;
        var ids = []
        for (let p in pids) {
            ids.push(parseInt(pids[p]))
        }
        var price = {}
        widget._rpc({
            model: 'purchase.order.line',
            method: 'search_read',
            fields: [
                'price_unit',
                'product_id',
                'product_qty',
                'order_id'
            ],
            domain: [
                ['product_id', 'in', ids],
                ['order_id.state', '=', 'purchase']
            ],
        }).then(function (result) {
            for (let p in result) {
                if (result[p].product_id[0] in price) {
                    if (result[p].price_unit in price[result[p].product_id[0]]) {
                        price[result[p].product_id[0]][result[p].price_unit] += result[p].product_qty
                    } else {
                        price[result[p].product_id[0]][result[p].price_unit] = result[p].product_qty
                    }
                } else {
                    price[result[p].product_id[0]] = {}
                    price[result[p].product_id[0]][result[p].price_unit] = result[p].product_qty
                }


            }

            for (var pid in price) {
                let str = ''
                for (var pr in price[pid]) {
                    str = str + '<span title="qta ' + price[pid][pr] + '">' + pr + '</span>   '
                }
                $('.price_' + pid).html(str)
            }
        });
    }

    var carico = AbstractAction.extend({
        start: function () {
            var this_carico = this
            this._rpc({
                model: 'res.partner',
                method: 'search_read',
                fields: [
                    'id',
                    'name'
                ],
                domain: [
                    ['supplier', '=', true],
                    ['active', '=', true],
                    ['parent_id', '=', false],
                    ['company_id', '=', parseInt(session.company_id)]
                ],
            }).then(function (suppliers) {
                var choose = new carico_choose(this_carico, suppliers);
                choose.appendTo(this_carico.$el);
            });
        },
    });

    var carico_choose = Widget.extend({
        //template : 'carico_choose',
        /*events : {
            "click #gotoCarico" : "GoToCarico",
            "change #c_supplier" : "SearchWave"
        },*/
        init: function (parent, suppliers) {
            this._super(parent);
            this.suppliers = suppliers;
            this.parent = parent;
        },
        start: function () {
            var this_choose = this;
            var options = {
                title: "Carico da Fornitore - ",
                subtitle: 'Scegli il Fornitore',
                size: 'large',
                dialogClass: '',
                $content: Qweb.render('carico_choose2', {suppliers: this.suppliers}),
                buttons: [{
                    text: _t("Chiudi"),
                    close: true,
                    classes: "btn-primary"
                }, {
                    text: "Avanti",
                    classes: "btn-success",
                    click: this.GoToCarico
                }]
            }
            var dial = new Dialog(this, options)
            dial.open()
            /*this.dial = new Dialog(this, options)
            this.dial.open();*/

            $(document).on('change', '#c_supplier', function (e) {
                this_choose.SearchWave(e);
            });
            /* $('#c_supplier').change(function (e) {
                 this_choose.SearchWave(e);
             })*/
            return this._super.apply(this, arguments);
        },
        GoToCarico: function (e) {
            var modal_content = e.currentTarget.closest('.modal-content');
            var supplier_id = $(modal_content).find('#c_supplier').val();
            var document_number = $(modal_content).find('#document_number').val();
            var batch = $(modal_content).find('#batchs_supplier').val();
            var this_choose = this;
            //this.close();
            var message = '';
            if (supplier_id == '') {
                message = message + "<li><b>Fornitore</b> mancante</li>";
            }
            if (document_number == '') {
                message = message + "<li><b>Numero Documento</b> mancante</li>";
            }

            if (batch != undefined) {
                document_number = $('#batchs_supplier option:selected').text();
                return this._rpc({
                    model: 'res.partner',
                    method: 'search_read',
                    fields: [
                        'id',
                        'name'
                    ],
                    domain: [
                        ['id', '=', parseInt(supplier_id)]
                    ],
                    limit: 1,
                }).then(function (sup) {
                    let supplier_name = sup != null && sup.length > 0 ? sup[0].name : "";
                    var nuovo = new carico_go(this_choose.getParent().parent, supplier_id, supplier_name, document_number, batch);
                    nuovo.appendTo('.o_content');
                    //this.destroy();
                    this_choose.close();
                });
            }

            if (message != '') {
                //return this.do_warn('ERRORE', message);
                this.do_warn("Errore", message);
            }

            return this._rpc({
                model: 'res.partner',
                method: 'search_read',
                fields: [
                    'id',
                    'name'
                ],
                domain: [
                    ['id', '=', parseInt(supplier_id)]
                ],
                limit: 1,
            }).then(function (sup) {
                return this_choose._rpc({
                    model: 'purchase.order',
                    method: 'search_read',
                    fields: [
                        'id',
                        'partner_id',
                        'picking_ids'
                    ],
                    domain: [
                        ['partner_id', '=', parseInt(supplier_id)],
                        ['state', '=', 'purchase']
                    ],
                }).then(function (pord) {
                    if (pord.length == 0) {
                        return this_choose.do_warn("NESSUN ORDINE", "Non esistono ordini di acquisto per il fornitore selezionato. Non puoi procedere oltre.");
                    }

                    var ids = [];
                    for (let i in pord) {
                        ids.push(pord[i].picking_ids);
                    }

                    this_choose._rpc({
                        model: 'stock.picking.batch',
                        method: 'create_purchase_list',
                        args: [
                            document_number,
                            ids
                        ],
                    }).then(function (result) {
                        batch = result.id
                        let supplier_name = sup != null && sup.length > 0 ? sup[0].name : "";
                        var nuovo = new carico_go(this_choose.getParent().parent, supplier_id, supplier_name, document_number, batch);
                        this_choose.$el.empty();
                        nuovo.appendTo(this_choose.$el);
                    });

                });
            });
        },
        SearchWave: function (e) {
            var sup_id = $(e.currentTarget).val()
            $('.batch_row').remove();
            return this._rpc({
                model: 'stock.picking.batch',
                method: 'search_read',
                fields: [
                    'id',
                    'name'
                ],
                domain: [
                    ['in_exit', '=', true],
                    ['state', '=', 'in_progress'],
                    ['picking_ids.partner_id', '=', parseInt(sup_id)]
                ],
            }).then(function (batchs) {
                if (batchs.length > 0) {
                    var html = '<tr class="oe_form_group_row batch_row"><td><b>Lista Aperta</b></td><td><select id="batchs_supplier">';
                    for (var i in batchs) {
                        html = html + '<option value="' + batchs[i].id + '" selected="selected">' + batchs[i].name + '</option>';
                    }
                    html = html = html + '</td></tr>';
                    $('.supplier_tr_row').after(html)
                }
            });
        }
    });

    var carico_go = Widget.extend({
        template: "carico_go",
        events: {
            "change #search": "doBarcode",
            "click #close_batch": "Validate"
        },
        init: function (parent, supplier_id, supplier_name, document_number, batch) {
            this._super(parent);
            var this_cgo = this;
            this.supplier_id = parseInt(supplier_id);
            this.document_number = document_number;
            this.batch = parseFloat(batch);
            this.supplier_name = supplier_name;
            this.products = {};
            this.products_ordered = {};
            this.pid = {}
            this._rpc({
                model: 'stock.picking.batch',
                method: 'search_read',
                fields: [
                    'id',
                    'name',
                    'picking_ids'
                ],
                domain: [['id', '=', this.batch]],
                limit: 1,
            }).then(function (result) {
                if (result != null && result.length > 0) {
                    this_cgo.document_number = result[0].name
                    var ids = []
                    for (let p in result[0].picking_ids) {
                        ids.push(result[0].picking_ids[p]);
                    }
                    // TODO remote call changed from stock.move.line to stock.move
                    this_cgo._rpc({
                        model: 'stock.move',
                        method: 'search_read',
                        fields: [
                            'id',
                            'product_id',
                            'product_uom_qty',
                            'quantity_done'
                        ],
                        domain: [
                            ['quantity_done', '>', 0],
                            ['picking_id', 'in', ids]
                        ],
                    }).then(function (line) {
                        var pqty = 0;

                        for (let l in line) {
                            this_cgo.pid[line[l].product_id[1]] = line[l].product_id[0];
                            pqty = pqty + parseInt(line[l].product_uom_qty)
                            if (line[l].product_id[1] in this_cgo.products) {
                                this_cgo.products[line[l].product_id[1]] = parseInt(this_cgo.products[line[l].product_id[1]]) + line[l].quantity_done;
                            } else {
                                this_cgo.products[line[l].product_id[1]] = line[l].quantity_done;
                            }
                            this_cgo.products_ordered[line[l].product_id[1]] = pqty

                        }
                        count_products(this_cgo)
                        list_products(this_cgo)
                    });
                }
            });
        },
        doBarcode: function (e) {
            var this_cgo = this;
            var barcode = $(e.currentTarget).val();

            var barcode_list = []
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

            var qta = parseInt($('#qta').val());

            $(e.currentTarget).val('').focus();
            $('#qta').val(1);

            if (qta < 0) {
                return this.do_warn("QUANTITA NEGATIVA", "La quantità caricata non può essere negativa");
            }

            this._rpc({
                model: 'stock.move',
                method: 'search_read',
                fields: [
                    'id',
                    'product_id',
                    'product_uom_qty',
                    'quantity_done'
                ],
                domain: [
                    ['picking_id.batch_id', '=', this.batch],
                    ['product_id.barcode', 'in', barcode_list]
                ],
            }).then(function (line) {
                var results = []
                var qty_residual = 0;
                var pqty = 0;
                var ids = [];
                for (let i in line) {
                    pqty = pqty + parseInt(line[i].product_uom_qty)
                    if (line[i].product_uom_qty > line[i].quantity_done) {
                        results.push(line[i])
                        qty_residual = qty_residual + line[i].product_uom_qty - line[i].quantity_done;
                        ids.push(line[i].id)
                    }
                }
                if (results.length == 0) {
                    return this_cgo.do_warn("BARCODE INESISTENTE", "Il prodotto non è presente nella lista di carico o è già stato caricato");
                }

                if (qta > qty_residual) {
                    return this_cgo.do_warn("QUANTITA MAGGIORE", "Puoi caricari al massimo <b>" + qty_residual + "</b> pezzi del prodotto. Contatta il tuo responsabile per i rimanenti.");
                }

                this_cgo._rpc({
                    model: 'stock.move',
                    method: 'complete_operation',
                    args: [
                        ids,
                        qta
                    ],
                });

                if (line[0].product_id[1] in this_cgo.products) {
                    this_cgo.products[line[0].product_id[1]] = parseInt(this_cgo.products[line[0].product_id[1]]) + qta;
                } else {
                    this_cgo.products[line[0].product_id[1]] = qta
                }
                this_cgo.products_ordered[line[0].product_id[1]] = pqty
                this_cgo.pid[line[0].product_id[1]] = line[0].product_id[0];

                this_cgo.do_notify("CARICATO", qta + ' x ' + line[0].product_id[1])

                $('#purchase_in_product_list tbody').html('');
                count_products(this_cgo)
                list_products(this_cgo)
            });
        },
        Validate: function (e) {
            this.do_notify("CARICO COMPLETO", '');
            $('.oe-cp-search-view').remove();
            $('#qta').remove();
            $('#close_batch').remove();
            this._rpc({
                model: 'stock.picking.batch',
                method: 'close_and_validate',
                args: [this.batch],
            });
        }
    });

    // Add to action_registry the reverse ClientAction Widget
    core.action_registry.add('netaddiction_warehouse.carico', carico);

});
