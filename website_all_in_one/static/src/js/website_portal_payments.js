odoo.define('website_all_in_one.website_portal_payments', function (require) {
"use strict";

var website = require('website.website');
var ajax = require('web.ajax');


// When clicking on payment button: create the tx using json then continue to the acquirer

$( ".o_radio_input" ).on( "click", function() {
  if($( ".o_radio_input:checked" ).length == 1)
  {
    $('#pay_partial_payment').prop('disabled', false);
  }
  else
  {
    $('#pay_partial_payment').prop('disabled', true);
  }  
});

var $payment = $(".o_website_payment");
$payment.on("click", 'button[type="submit"],button[name="submit"]', function (ev) {
  ev.preventDefault();
  ev.stopPropagation();
  $(ev.currentTarget).attr('disabled', true);
  $(ev.currentTarget).prepend('<i class="fa fa-refresh fa-spin"></i> ');
  var $form = $(ev.currentTarget).parents('form');
  var data =$("div[class~='o_website_payment_new_payment']").data();
  ajax.jsonRpc('/website_all_in_one/transaction/', 'call', data).then(function (result) {
    $form.submit();
  });

  function getFormData($form){
      var unindexed_array = $form.serializeArray();
      var indexed_array = {};

      $.map(unindexed_array, function(n, i){
          indexed_array[n.name] = n.value;
      });

      return indexed_array;
  }
});


});
