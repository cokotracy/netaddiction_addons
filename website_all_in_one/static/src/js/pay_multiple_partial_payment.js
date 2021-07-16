odoo.define('website_all_in_one.pay_multiple_partial_payment', function(require) {
    "use strict";

    var core = require('web.core');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var request
    var _t = core._t;
    var invoice_data = false

    $(document).ready(function(){
        $("#pay_multiple_partial").click(function(ev){
            var invoice_ids = []
            var $form = $(ev.currentTarget).parents('form');
            $('.o_portal_my_doc_table input[type="checkbox"]:checked').each(function(){
                var id = $(this).attr('value');
                invoice_ids.push(id)
            });
            document.getElementById("invoice").value = invoice_ids;
        });
    });

    $(document).ready(function(){
        $("#amount").focusout(function(ev){
            
            var $form = $(ev.currentTarget).parents('form');
            
            var fistInput = document.getElementById("amount").value;
            var secondInput = document.getElementById("total_amount").value;

            if (parseFloat(fistInput) > parseFloat(secondInput)) 
            {
                document.getElementById("amount").value = null;
                document.getElementById("amount").style.borderColor = "red";
                alert('you can not pay more than amount');            
            }
            else{
                document.getElementById("amount").style.borderColor = null;
            }
        });

    });

    $(document).ready(function(){
        $("#amount1").focusout(function(ev){
            
            var $form = $(ev.currentTarget).parents('form');
            
            var fistInput = document.getElementById("amount1").value;
            var secondInput = document.getElementById("total_amount1").value;

            if (parseFloat(fistInput) > parseFloat(secondInput)) 
            {
                document.getElementById("amount1").value = null;
                document.getElementById("amount1").style.borderColor = "red";
                alert('you can not pay more than amount');            
            }
            else{
                document.getElementById("amount1").style.borderColor = null;
            }
        });

    });
});