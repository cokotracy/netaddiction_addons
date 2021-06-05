odoo.define("web_onchange_enterkey.FieldChar", function(require) {
    "use strict";

    var basic_fields = require("web.basic_fields");

    var FieldCharEnterOnChange = {
        /**
         * Override that check inside this.attrs if exists special keys
         * onchange_enterkey and onchange_clear.
         * if enter is pressed and special attr is set trigger up onchange
         * without removing focus.
         *
         * onchange_clear attr will clear the input without trigger another
         * onchange event
         * @param event
         * @returns {*}
         * @private
         */
        _onKeydown: function(event) {
            // example <field name="your-field-name" onchange_enterkey="1"/>
            if ((event.keyCode === 13)
                && (Number(this.attrs.onchange_enterkey))
                && (this.attrs.on_change)) {
                this.commitChanges();
                // example <field name="your-field-name" onchange_enterkey="1" onchange_clear="1"/>
                if (Number(this.attrs.onchange_clear)) {
                    this.$el.val('');
                }
            }
            return this._super.apply(this, arguments);
        },
    };

    // Apply only to FieldChar because FieldText uses carriage return
    basic_fields.FieldChar.include(FieldCharEnterOnChange);

    return {
        FieldCharEnterOnChange: FieldCharEnterOnChange,
    };
});
