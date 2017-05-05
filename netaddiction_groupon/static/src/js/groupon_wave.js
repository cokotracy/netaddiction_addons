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
        var groupon = new Model('groupon.pickup.wave');
        core.qweb.add_template("/netaddiction_groupon/static/src/xml/groupon_template.xml");
        function groupon_pickup(barcode){
            $('.done_msg').remove();
            $('.orange_msg').remove();
            $('.error_msg').remove();
            $('#result_shelfs').remove();
            var products = new Array();
            $('.product_row').each(function(index,value){
                if($(value).attr('data-barcode') == barcode){
                    products.push(value)
                }
            });
            if(products.length==0){
                //aggiunge zero
                barcode = '0'+barcode
                $('.product_row').each(function(index,value){
                    if($(value).attr('data-barcode') == barcode){
                        products.push(value)
                        $('#barcode').val(barcode)
                    }
                }); 
            }
            if(products.length==0){
                //toglie zero
                barcode = barcode.replace(/^0+/, '');
                $('.product_row').each(function(index,value){
                    if($(value).attr('data-barcode') == barcode){
                        products.push(value)
                        $('#barcode').val(barcode)
                    }
                }); 
            }
            if(products.length==0){
                //capitalize
                barcode = barcode.toLowerCase();
                barcode = barcode.charAt(0).toUpperCase() + barcode.slice(1);
                $('.product_row').each(function(index,value){
                    if($(value).attr('data-barcode') == barcode){
                        products.push(value)
                        $('#barcode').val(barcode)
                    }
                }); 
            }
            if(products.length==0){
                //upper
                barcode = barcode.toUpperCase();
                $('.product_row').each(function(index,value){
                    if($(value).attr('data-barcode') == barcode){
                        products.push(value)
                        $('#barcode').val(barcode)
                    }
                }); 
            }
            if(products.length==0){
                //lower
                barcode = barcode.toLowerCase();
                $('.product_row').each(function(index,value){
                    if($(value).attr('data-barcode') == barcode){
                        products.push(value);
                        $('#barcode').val(barcode);
                    }
                }); 
            }

            if(products.length==0){
                NotifyVibrate();
                NotifyPlay();
                if($('.error_msg').length){
                    $('.error_msg').text('Barcode non trovato nella lista');
                }else{
                    put_error('Barcode non trovato nella lista');
                }
                return true;
            }else{
                var href = window.location.href;
                var wave_id = href.substr(href.lastIndexOf('/') + 1);
                wave_id = wave_id.replace(/\D/g,'');
                pid = $(products[0]).attr('data-pid');
                if(products.length>1){
                    var shelfs = [];
                    $.each(products, function(i,v){
                        shelfs.push({'id':$(v).attr('data-shelf-id'), 'name': $(v).attr('data-shelf')});
                    });
                    $('#barcode-block').before(core.qweb.render("grouponshelfs_choice",{shelfs : shelfs, pid: pid, wave: wave_id}));
                }else{
                    var shelf = $(products[0]).attr('data-shelf-id');
                    decrease_shelf(shelf, pid, wave_id);
                }
                
            }

        }

        $('#content').on('click', '.shelf_pick', function(e){
            var target = e.currentTarget;
            var shelf = $(target).attr('data-ids');
            var pid = $(target).attr('data-pid');
            var wave = $(target).attr('data-wave');
            decrease_shelf(shelf, pid, wave);
            return false;
        });

        $('#search_barcode').on('click', function(e) {
            var barcode = $('#barcode').val();
            groupon_pickup(barcode);
        });

        function put_error(msg){
            html = '<div class="error_msg">'+msg+'</div>';
            $('#barcode-block').before(html);
            window.setTimeout(function() {window.scrollTo('.error_msg',{duration:'slow'});}, 0);
        }

        function decrease_shelf(shelf, product_id, wave_id){
            $('#result_shelfs').remove();
            $('.product_row').each(function(index,value){
                if($(value).attr('data-pid') == product_id && $(value).attr('data-shelf-id')==shelf){
                    var qty_to_down = $(value).find('.qty_for_shelf').text();
                    groupon.call('pickup_product', [wave_id, product_id, shelf, qty_to_down]).then(function(results){
                        if(results['result']==0){
                            put_error(results['error']);
                        }else{
                            var nome_ripiano = $(value).attr('data-shelf');
                            
                            $('#barcode-block').before('<div class="done_msg">Hai scaricato <b>'+qty_to_down+'</b> - '+$(value).find('.name_pid').text()+' da <b>'+nome_ripiano+'</b></div>');
                            window.setTimeout(function() {window.scrollTo(value,{duration:0});}, 0);
                            $(value).css('background-color','#87D37C').slideUp(1000);
                            block = $(value).closest('.block');
                            setTimeout(function() {
                                $(value).remove();
                                var lol = $(block).find('.product_row');
                                if(lol.length==1){
                                    $(this).closest('.block').slideUp(1000)
                                }
                            }, 1000);
                            
                            window.setTimeout(function() {window.scrollTo('.done_msg',{duration:'slow'});}, 0);
                        }
                    });
                }
            });
            return false;
        }

    });
});