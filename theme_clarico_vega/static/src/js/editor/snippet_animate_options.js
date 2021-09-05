//--------------------------------------------------------------------------
// Snippet Aos Animation customize Options and Expertise Progress bar 
//--------------------------------------------------------------------------
odoo.define('theme_clarico_vega.snippetEpt', function (require) {
	'use strict';
	var SnippetOption = require('web_editor.snippets.options');

    SnippetOption.Class.include({
        selectClass: async function (previewMode, widgetValue, params) {
            await this._super(...arguments);
            const aos = 'aosData' in params ? params.aosData : false;
            if(aos) {
                this.$target.attr('data_aos_ept',aos);
            }
        },
    });
});
