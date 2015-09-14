"use strict";

openerp.netaddiction_doozy = function(instance) {

    // Lista dei moduli JS di NetAddiction Doozy da caricare all'avvio
    var submodules = [
        'decimal_precision'
    ];

    submodules.forEach(function(submodule) {
        instance.netaddiction_doozy[submodule](instance);
    });

};

openerp.netaddiction_doozy.decimal_precision = function(instance) {

    // Lista dei campi float a cui togliere i decimali
    var float_to_int = [
        'avail_qty',
        'min_quantity',
        'min_qty',
        'produce_delay',
        'quant',
        'quantity',
        'qty',
        'sale_delay',
        'warranty'
    ];

    /* IntegerFieldFloat */

    instance.netaddiction_doozy.IntegerFieldFloat = instance.web.form.FieldFloat.extend({
        init: function(field_manager, node) {
            this._super.apply(this, [field_manager, node]);

            if(float_to_int.indexOf(this.name) != -1) {
                if(typeof this.digits != 'undefined') {
                    this.digits = [this.digits[0], 0];
                } else {
                    this.digits = [16, 0];
                }
            }
        }
    });

    instance.web.form.widgets.add('float', 'instance.netaddiction_doozy.IntegerFieldFloat');

    /* IntegerColumn */

    instance.netaddiction_doozy.IntegerColumn = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            var value = this._super.apply(this, [row_data, options]);

            if(float_to_int.indexOf(this.name) != -1) {
                value = parseInt(value);
            }

            return value;
        }
    });

    instance.web.list.columns.add('field', 'instance.netaddiction_doozy.IntegerColumn');

};
