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

		$("#submit_review").click(function(ev){
			
			ajax.jsonRpc('/submit_review/', 'call', {

			}).then(function (json_data) {
				if(json_data){
					alert("You can do a review only if you had at least one sale order in done state.!!");
					ev.preventDefault();
					location.reload();
               		return false;
					}
				})
			})

	})

});