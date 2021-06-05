odoo.define('affiliate_management.validation',function(require){
"use strict";

var core = require('web.core');
var ajax = require('web.ajax');

var _t = core._t;

  // js for choose button in step 2 of generate product url

// term_condition










$(document).ready(function() {
    $('.signup-btn').on('click',function(){
        var c = $('#tc-signup-checkbox').is(':checked');
        console.log(c);
        if (c == false)
        {

            $('#term_condition_error').show();
            return false;
        }
      });



	$( ".button_image_generate_url" ).hide();
	$('.o_form_radio').on('click',function(){
    $('[id^=product-text_]').hide();
		console.log(this.getAttribute('id').split("_")[1])
		var radio_id = this.getAttribute('id').split("_")[1];
		$( ".button_image_generate_url" ).hide();
		$('#image_'+radio_id).show();

	});
	$('.o_form_radio_product').on('click',function(){
		$( ".button_image_generate_url" ).hide();
    var product_text_id =$("#product-text_"+this.id.split("_")[1]);
    $(product_text_id).show();
	});


// copy the text from clipboard
  var copyBtn
  var input

  $('[id^=copy-btn_]').on('click',function(){
      console.log("start")
      copyBtn = this;
      input = $("#copy-me_"+this.id.split("_")[1]);
      console.log("input",input)
      copyToClipboard();
      $('[id^=copy-btn_]').text('Copy to Clipboard')
      $(this).text('copied');
      console.log("copy button clicked")
    });

  function copyToClipboardFF(text) {
    window.prompt ("Copy to clipboard: Ctrl C, Enter", text);
  }

  function copyToClipboard() {
    var success   = true,
        range     = document.createRange(),
        selection;

  // For IE.
  if (window.clipboardData) {
    console.log("clipboard")
    window.clipboardData.setData("Text", input.val());
  } else {
    // Create a temporary element off screen.
    var tmpElem = $('<div>');
    tmpElem.css({
      position: "absolute",
      left:     "-1000px",
      top:      "-1000px",
    });
    // Add the input value to the temp element.
    tmpElem.text(input.val());
    console.log("tmpElem",tmpElem)
    $("body").append(tmpElem);
    // Select temp element.
    range.selectNodeContents(tmpElem.get(0));
    console.log("range",range)
    selection = window.getSelection ();
    selection.removeAllRanges ();
    console.log("remove range")
    selection.addRange (range);
    // Lets copy.
    try {
      success = document.execCommand ("copy", false, null);
    }
    catch (e) {
      copyToClipboardFF(input.val());
    }
    if (success) {
      // alert ("The text is on the clipboard, try to paste it!");
      // remove temp element.
      tmpElem.remove();
    }
  }
}


// copy link for affiliate link generator
$("#link_copy_button").click(function(){
  $("#copy_link").show();
    $("#copy_link").select();
    document.execCommand('copy');
    $("#copy_link").hide();
});
// copy html code from text area
var clicked = false;
$("#banner_copy_button").click(function(){
    $("#banner_html_code").select();
    document.execCommand('copy');
    $(this).text('copied');
    if (clicked == false)
    {
          $('#step3').hide();
          $('#step3').after(
              "<span class='step1'>&#10003;</span>"
            );
          clicked = true;
  }


});

$("#later_button").click(function(){
    $("#aff_req_btn").hide();
});




$('[id^=yes_btn_uid_]').on('click',function(){
     var uid = this.id.split("_")[3];
     ajax.jsonRpc("/affiliate/request", 'call',{'user_id': uid}).then(function (result){
            console.log(result);
            if (result)
            {
              // $("#aff_req_btn").replaceWith( "<p class='alert alert-success'>Your Request has been submitted sucessfully. Soon you will be notify by email.</p>");
              $("#aff_req_btn").hide();
              $(".alert_msg_banner").show();

            }
              else{

                }
          });
    });

function isValidEmailAddress(emailAddress) {
    // var pattern = /^([a-z\d!#$%&'*+\-\/=?^_`{|}~\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]+(\.[a-z\d!#$%&'*+\-\/=?^_`{|}~\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]+)*|"((([ \t]*\r\n)?[ \t]+)?([\x01-\x08\x0b\x0c\x0e-\x1f\x7f\x21\x23-\x5b\x5d-\x7e\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]|\\[\x01-\x09\x0b\x0c\x0d-\x7f\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))*(([ \t]*\r\n)?[ \t]+)?")@(([a-z\d\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]|[a-z\d\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF][a-z\d\-._~\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]*[a-z\d\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])\.)+([a-z\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]|[a-z\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF][a-z\d\-._~\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]*[a-z\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])\.?$/i;
    var pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}$/i;
    return pattern.test(emailAddress);
};

    $("#join-btn").click(function(){
      var email = $('#register_login').val();
      if (isValidEmailAddress(email)){
          $('.affiliate_loader').show();
          ajax.jsonRpc("/affiliate/join", 'call',{'email': email}).then(function (result){
            if (result){
                console.log(result);
                $(".aff_box").replaceWith(
                  "<div class='alert_msg_banner_signup' style='margin-top:10px;'>\
                  <center>\
                    <span style='color:white'>\
                      <img src='/affiliate_management/static/src/img/Icon_tick.png' />&nbsp;<span>"+result+"</span>\
                    </span>\
                    </center>\
                  </div>\
                  <br/>\
                 <div id='aff_req_btn'>\
                    <center>\
                      <a href='/shop' class='btn btn-success' style='width:177px;height:37px;' >Continue Shopping</a>\
                   </center>\
                 </div>");
            }
          });
          $('.affiliate_loader').hide();
          return false;
      }else{
        console.log("wrong email");
        alert("Invalid Email type");
        return false;
      }

    });


    $("#cpy_cde").click(function(){
      $("#usr_aff_code").select();
      $(this).text('copied');
      document.execCommand('copy');

      return false;
    });

    $("#cpy_url").click(function(){
      $("#usr_aff_url").select();
      $(this).text('copied')
      document.execCommand('copy');
      return false;
    });


    $("#url_anchor").click(function(){
      $("#affiliate_url_inp").show();
      $("#affiliate_code_inp").hide();
      return false;
    });


    $("#code_anchor").click(function(){
      $("#affiliate_url_inp").hide();
      $("#affiliate_code_inp").show();
      return false;
    });

});

});
