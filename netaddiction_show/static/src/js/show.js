window.BarcodeData = function(barcode, type, typeText) {
    barcode = $('#barcode').val(barcode);
    $('#search_barcode').trigger('click');
};

window.NotifyVibrate = function(){
    WebHub.Notify.vibrate();
}
window.NotifyBeep = function(){
    WebHub.Notify.beep();
}
window.PlayFailed = function(errorCode, errorDescription){
    alert("Play failed ("+errorCode+"): "+errorDescription);
}
window.NotifyPlay = function(){
    //TODO: cambiare con l'url dell'app in produzione
    WebHub.Notify.play("https://"+window.location.hostname+"/netaddiction_warehouse/static/src/beep-03.mp3",WebHub.Folder.NONE,PlayFailed);
}
window.NotifyMessage = function(message,response,function_dismissed){
    WebHub.Notify.message("",message,response,function_dismissed);
}
$(document).ready(function(){

    odoo.define('netaddiction_show_app', function (require) {
        var utils = require('web.utils');
        var Model = require('web.Model');
        var core = require('web.core');

        core.qweb.add_template("/netaddiction_warehouse/static/src/xml/search.xml");
        core.qweb.add_template("/netaddiction_warehouse/static/src/xml/allocation.xml");
        core.qweb.add_template("/netaddiction_show/static/src/xml/template_show.xml");

        var product = new Model('product.product');
        var show_model = new Model('netaddiction.show');

        function get_allocation(barcode){
            $('.error_msg').remove();
            $('.done_msg').remove();
            $('#sup_text').remove();
            var barcode_list = []
            barcode_list.push(barcode)
            barcode = '0'+barcode
            barcode_list.push(barcode)
            barcode = barcode.replace(/^0+/, '');
            barcode_list.push(barcode)
            barcode = barcode.toLowerCase();
            barcode_list.push(barcode)
            barcode = barcode.charAt(0).toUpperCase() + barcode.slice(1);
            barcode_list.push(barcode)
            barcode = barcode.toUpperCase();
            barcode_list.push(barcode)
            product.call('get_json_allocation',[barcode_list]).then(function(result){
                if(result.result == 0){
                    $('#result').html('');
                    NotifyVibrate()
                    NotifyPlay()
                    if($('.error_msg').length){
                        $('.error_msg').text(result.error);
                    }else{
                        $('#barcode_form').before(core.qweb.render("Error",{error : result.error}));
                    }
                }else{
                    $('.error_msg').remove();
                    $('#result').before('<p id="sup_text">Scegli il ripiano da cui spostare la quantità desiderata</p>');
                    $('#result').html(core.qweb.render("block_new_allocation_show",{shelf : result}));
                }
            });
        }

        window.select_shelf_to_move = function(elem){
            $('.hide_content').hide();
            $('.modify').closest('.block').find('.block_title').removeClass('block_title modify').addClass('block_content');
            $(elem).find('.block_content').removeClass('block_content').addClass('block_title modify');
            $(elem).find('.hide_content').removeClass('block_title').addClass('block_content').show();
        }

        window.move_shelf = function(all,elem){
            $('.error_msg').remove();
            $('.done_msg').remove();
            $('#sup_text').remove();
            var qta = $(elem).closest('.hide_content').find('.qta').val();
            var show_id = $('#show_id').val();
            show_model.call('add_quant_to_show',[all,qta,show_id]).then(function(result){
                if(result != 1){
                    NotifyVibrate()
                    NotifyPlay()
                    $('#barcode_form').before(core.qweb.render("Error",{error : result}));
                }else{
                    $('#barcode_form').before('<div class="done_msg">PRODOTTO SPOSTATO IN FIERA</div>');
                }
            });
        }

        $('#search_barcode').on('click', function(e) {
            var barcode = $('#barcode').val();
            get_allocation(barcode);
        });

    });
});