//--------------------------------------------------------------------------
// Contains Aos animation editor js
//--------------------------------------------------------------------------
odoo.define('theme_clarico_vega.s_editor_js', function (require) {
	'use strict';
	var EditorMenuBar = require("web_editor.editor");
	
	 EditorMenuBar.Class.include({
		save: async function (reload) {
	        var self = this;
	        var defs = [];
	        $('div,section').removeClass('aos-animate');
	        $("div[data_aos_ept],section[data_aos_ept]").each(function(){
				var data_aos_ept = $(this).attr('data_aos_ept');
				if(data_aos_ept){
	 				$(this).attr('data-aos',data_aos_ept);
					$(this).removeAttr('data_aos_ept');
				}
	    	});    
	        this.trigger_up('ready_to_save', {defs: defs});
            await Promise.all(defs);

            if (this.snippetsMenu) {
                await this.snippetsMenu.cleanForSave();
            }
            await this.getParent().saveModifiedImages(this.rte.editable());
            await this.rte.save();

            if (reload !== false) {
                return this._reload();
            }
	    },

        /* To make the hotspot elements Draggable in Edit Mode */
	    start: function () {
            var self = this;
            var def = this._super.apply(this, arguments);
            return def.then(() => {
                $("body section.hotspot_element").each(function(){
                    $(this).draggable({
                        containment: 'parent',
                        opacity: 0.4,
                        scroll: false,
                        revertDuration: 200,
                        refreshPositions: true,
//                        drag: function () {
//                            var esc = $.Event("keydown", { keyCode: 27 });
//                            $("body").trigger(esc);
//                        },
                        stop: function () {
                            var l = ( 100 * parseFloat($(this).position().left / parseFloat($(this).parent().width())) ) + "%" ;
                            var t = ( 100 * parseFloat($(this).position().top / parseFloat($(this).parent().height())) ) + "%" ;
                            $(this).css("left", l);
                            $(this).css("top", t);
//                            $('body.editor_enable').removeClass('o_fullscreen')
//                            var esc = $.Event("keydown", { keyCode: 27 });
//                            $("body").trigger(esc);
                        }
                    })
                });
            })
        },

	});
});
