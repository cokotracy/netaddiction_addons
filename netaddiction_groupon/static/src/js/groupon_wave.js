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

    odoo.define('netaddiction_groupon_wave', function (require) {
        var utils = require('web.utils');
        var Model = require('web.Model');
        var core = require('web.core');


        var product = new Model('product.product');
        var show_model = new Model('netaddiction.show');

        function get_allocation(barcode){
            console.log(barcode)
        }

        $('#search_barcode').on('click', function(e) {
            var barcode = $('#barcode').val();
            get_allocation(barcode);
        });

    });
});