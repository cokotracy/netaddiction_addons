odoo.define('netaddiction_warehouse.spara_pacchi', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var Dialog = require('web.Dialog');
    // var Notification = require('web.Notification');
    var _t = core._t;
    var qweb = core.qweb;

    var AbstractAction = require('web.AbstractAction');

    var spara_pacchi = AbstractAction.extend({
        init: function (parent, action, options) {
            console.log("Reverse AbstractAction");
            this._super.apply(this, arguments);
            this.action = action;
            this.parent = parent;
            this.dialog;
        },
        start: function () {
            this._super.apply(this, arguments);
            var rev = this;
            this._rpc({
                model: 'delivery.carrier',
                method: 'search_read',
                fields: ['id', 'name'],
            }).then(function (carriers) {
                var options = {
                    title: "Spara Pacchi",
                    subtitle: 'Scegli il Corriere',
                    size: 'large',
                    dialogClass: '',
                    $content: qweb.render('dialog_content_spara_pacchi', {carriers: carriers}),
                    buttons: [{
                        text: _t("Chiudi"),
                        close: true,
                        classes: "btn-primary"
                    }, {
                        text: "Avanti",
                        classes: "btn-success",
                        click: function () {
                            return rev.goNext();
                        }
                    }]
                }
                rev.dialog = new Dialog(this, options);
                rev.dialog.open();
            });
        },
        goNext: function () {
            var carrier = $('#select_carrier').val();
            var name = $('#select_carrier :selected').text();
            var carrier_selected = {
                'id': carrier,
                'name': name
            }
            var carrier_manifest = new Carrier_Spara_Pacchi(this, carrier_selected);
            carrier_manifest.appendTo('.o_content');
            this.dialog.close();
        }
    });

    var Carrier_Spara_Pacchi = Widget.extend({
        template: 'carrier_spara_pacchi',
        events: {
            'change #search': 'verifyBarcode',
            'click #sblocca': 'go_next'
        },
        init: function (parent, carrier) {
            this._super(parent);
            this.carrier = carrier;
            this.manifest = 0;
            this.buzz = new Audio("/netaddiction_warehouse/static/src/beep-03.mp3");
            this.more_buzz = new Audio("/netaddiction_warehouse/static/src/beep-05.mp3");
            this.ok_buzz = new Audio("/netaddiction_warehouse/static/src/beep-02.mp3");
            this.table = null;
            var today = new Date();
            var dd = today.getDate();
            var mm = today.getMonth() + 1;
            if (mm < 10) {
                mm = '0' + mm;
            }
            if (dd < 10) {
                dd = '0' + dd
            }
            var yyyy = today.getFullYear();
            this.date = yyyy + '-' + mm + '-' + dd;
            var obj = this;
            this._rpc({
                model: 'netaddiction.manifest',
                method: 'search_read',
                fields: [],
                domain: [
                    ['date', '=', this.date],
                    ['carrier_id.id', '=', this.carrier['id']]
                ],
                limit: 1,
            }).then(function (result) {
                if (result == null || result.length === 0) {
                    let title = 'ERRORE';
                    let text = 'OGGI NON CI SONO PACCHI';
                    return obj.do_warn(title, text);
                }
                obj.manifest = result[0].id;
                obj.table = new Table_Shipping(obj, result[0].id)
            });
        },
        go_next: function () {
            var manifest = this.manifest;
            var father = this;
            var psw = $('#psw_block').val()
            if (psw == 'pippo123') {
                $('#psw_block').val('')
                $('.o_content').css('background', 'white')
                $('.o_content').children().show()
                $('#message_box').hide()
                $('#search').val('').focus();
                if (father.table) {
                    father.table.destroy();
                }
                father.table = new Table_Shipping(father, manifest);
            } else {
                let title = 'ERRORE PSW';
                let text = 'PASSWORD ERRATA';
                return father.do_warn(title, text);
            }

        },
        stopProcess: function (message) {
            $('.o_content').children().hide()
            $('.o_content').css('background', '#6C7A89')
            $('#message_text').text(message)
            $('#message_box').show()

        },
        verifyBarcode: function (e) {
            var self = this
            var manifest = this.manifest;
            var buzz = this.buzz;
            var more_buzz = this.more_buzz;
            var ok_buzz = this.ok_buzz;
            var father = this;
            var barcode = $(e.currentTarget).val();
            var query = ['id', 'name', 'partner_id', 'delivery_read_manifest', 'delivery_barcode', 'manifest', 'origin'];
            var filter = [['delivery_barcode', '=', barcode], ['manifest.id', '=', parseInt(manifest)]];
            this._rpc({
                model: 'stock.picking',
                method: 'search_read',
                fields: query,
                domain: filter,
                limit: 1,
            }).then(function (picking) {
                if (picking == null || picking.length === 0) {
                    let title = 'ERRORE';
                    let text = 'IL BARCODE NON APPARTIENE AL MANIFEST DI OGGI';

                    more_buzz.play();
                    $('#search').val('').focus();
                    self.stopProcess(text)
                    return father.do_warn(title, text);
                }

                if (picking[0].delivery_read_manifest == true) {
                    let title = 'PACCO GIA\' SPARATO';
                    let text = 'HAI GIA\' SPARATO IL PACCO';
                    more_buzz.play();
                    $('#search').val('').focus();
                    self.stopProcess(text)
                    return self.do_warn(title, text);
                }
                self._rpc({
                    model: 'stock.picking',
                    method: 'confirm_reading_manifest',
                    args: [picking[0].id],
                }).then(function (e) {
                    if (e.state == 'problem') {
                        let title = 'ERRORE';
                        let text = e.message;

                        more_buzz.play();
                        self.stopProcess(text)
                        var error_html = picking[0].partner_id + ' ' + picking[0].delivery_barcode + ' ' + picking[0].origin + ' - ' + not.text + '<br/>'
                        $('#content_error').append(error_html)
                        return self.do_warn(title, text);
                    } else {
                        father.table.destroy();
                        father.table = new Table_Shipping(father, manifest);
                        ok_buzz.play();
                    }
                });

                $('#search').val('').focus();
            });
        },

    });

    var Table_Shipping = Widget.extend({
        template: 'table',
        init: function (parent, manifest) {
            this._super(parent);
            this.picks = [];
            this.read = [];
            var obj = this;
            var query = ['id', 'name', 'partner_id', 'delivery_read_manifest', 'delivery_barcode', 'manifest', 'origin'];
            var filter = [['manifest.id', '=', parseInt(manifest)]];
            this._rpc({
                model: 'stock.picking',
                method: 'search_read',
                fields: query,
                domain: filter,
            }).then(function (result) {
                var read = []
                var not_read = []
                $(result).each(function (index, value) {
                    if (value.delivery_read_manifest == 1) {
                        read.push(value)
                    } else {
                        not_read.push(value)
                    }
                })
                obj.picks = not_read;
                obj.read = read
                $('#residual_pick').text(not_read.length);
                $('#number_pick').text(read.length);
                obj.appendTo('#content_spara_pacchi');
            });
        }
    });

    core.action_registry.add("netaddiction_warehouse.spara_pacchi", spara_pacchi);
})
