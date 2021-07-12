console.log("custom js caleedddddddddddddddddddddddddddddddddd odoo_website_search_suggestion");
odoo.define('website_all_in_one.search_suggestion', function(require) {
    "use strict";

	var ajax = require('web.ajax');
	var core = require('web.core');
	var base = require('web_editor.base');
	var animation = require('website.content.snippets.animation');

	var qweb = core.qweb;
    var _t = core._t;

    var ajax = require('web.ajax');
    //var oe_website_sale = this;

	animation.registry.OdooWebsiteSearchSuggestion = animation.Class.extend({
		selector: ".search-query",
		start: function () {
		    console.log("start caleedddddddddddddddddddddddddddddddddd")
		    var self = this;
		    console.log("start caleedddddddddddddddddddddddddddddddddd",this.$target.typeahead)
		    this.$target.attr("autocomplete","off");
            this.$target.parent().addClass("typeahead__container");
            
            
            this.$target.typeahead({
            	minLength: 1,
				maxItem: 15,
				group: ["category", "{{group}}"],
				delay: 500,
				order: "asc",
				hint: true,
				dynamic:true,
				display: ["product", "category"],
				maxItemPerGroup: 5,
                template: '<span>' +
                          '<span>{{product}}</span>' +
                          '</span>',
                source:{ product:{ url: [{ type : "GET", url : "/search/suggestion", data : { query : "{{query}}"},},"data.product"] },},
              });
              
              
              //console.log("222222222222222222 caleedddddddddddddddddddddddddddddddddd",this.$target)
              
		    
		},
		
		
		callback: {
		    onClickAfter: function (node, a, item, event) {
	 
		        event.preventDefault;
	 
		        // href key gets added inside item from options.href configuration
		        alert(item.href);
	 
		    }
		},
		debug: true
		
	});


});;
