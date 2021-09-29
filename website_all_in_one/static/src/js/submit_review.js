odoo.define('website_all_in_one.submit_review', function (require) {
'use strict';
	require('web.dom_ready');
	var core = require('web.core');
	var ajax = require('web.ajax');
	var rpc = require('web.rpc');
	var QWeb = core.qweb;
	var request
	var _t = core._t;
	let from_date = 0
	$(document).ready(function(){

	    $(".review_font").click(function(ev){
	    	if ($("#nav_tabs_link_ratings_reviews").length > 0){
                var header_height = 10;
                if($('header#top').length && !$('header').hasClass('o_header_sidebar')) {
                    if($('header nav').hasClass('te_header_navbar')) {
                        this.header_height = $('header nav').height() + 30;
                    } else {
                        this.header_height = $('header').height() + 30;
                    }
                }
                var totalHeight = parseInt($("#te_product_tabs").offset().top) - parseInt(header_height) - parseInt($("#te_product_tabs").outerHeight());
                if ($(window).width() < 768)
                    totalHeight += 120;
                $([document.documentElement, document.body]).animate({
                    scrollTop: totalHeight
                }, 2000);
                $('#nav_tabs_link_ratings_reviews').trigger('click');
            }
	    });

		$("#submit_review").click(function(ev){
			
			ajax.jsonRpc('/submit_review/', 'call', {

			}).then(function (json_data) {
				if(json_data){
					alert("Non puoi recensire il prodotto se non hai completato l'acquisto!");
					ev.preventDefault();
					location.reload();
               		return false;
					}
				})
			})

	})

});