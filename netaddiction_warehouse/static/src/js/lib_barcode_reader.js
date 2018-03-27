window.BarcodeData = function(barcode, type, typeText) {
	barcode = $('#barcode').val(barcode);
    $('#barcode-form').trigger('submit');
};

window.NotifyVibrate = function(){
    WebHub.Notify.vibrate();
}
window.NotifyBeep = function(){
    var buzz = new Audio("https://"+window.location.hostname+"/netaddiction_warehouse/static/src/beep-05.mp3");
    buzz.play();
    //WebHub.Notify.beep();
}
window.PlayFailed = function(errorCode, errorDescription){
    alert("Play failed ("+errorCode+"): "+errorDescription);
}
window.NotifyPlay = function(){
    //TODO: cambiare con l'url dell'app in produzione
    var buzz = new Audio("https://"+window.location.hostname+"/netaddiction_warehouse/static/src/beep-05.mp3");
    buzz.play();
    //WebHub.Notify.play("https://"+window.location.hostname+"/netaddiction_warehouse/static/src/beep-03.mp3",WebHub.Folder.NONE,PlayFailed);
}
window.NotifyMessage = function(message,response,function_dismissed){
    WebHub.Notify.message("",message,response,function_dismissed);
}

window.submitform = function(e){
    if(e != ''){
         e.preventDefault();
    }
   
    barcode = $('#barcode').val();
    func = $('#barcode').attr('data-function');
    odoo_function[func](barcode);

}

window.response_message = function(index){
    $('#result_shelfs').remove();
    var href = window.location.href;
    var wave_id = href.substr(href.lastIndexOf('/') + 1);
    wave_id = wave_id.replace(/\D/g,'');
    console.log(wave_id)
    odoo_function['set_pick_up'](wave_id,window.shelfs[index]['id'],$('#barcode').val(),window.shelfs[index]['qty'])
}


$(document).ready(function(){

    odoo.define('netaddiction_warehouse', function (require) {
        var utils = require('web.utils');
        var Model = require('web.Model');
        var core = require('web.core');

        core.qweb.add_template("/netaddiction_warehouse/static/src/xml/search.xml");
        core.qweb.add_template("/netaddiction_warehouse/static/src/xml/allocation.xml");
        core.qweb.add_template("/netaddiction_warehouse/static/src/xml/pickup.xml");
        // do things with utils and Model
        var product = new Model('product.product');
        var allocations = new Model('netaddiction.wh.locations.line');
        var wave = new Model('stock.picking.wave');
        var picking = new Model('stock.picking');

        odoo_function ={
        	'get_allocation': function get_allocation(barcode){
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
					                        $('#barcode-form').before(core.qweb.render("Error",{error : result.error}));
					                    }
					                }else{
                                        $('.error_msg').remove();
					                    $('#result').html(core.qweb.render("block_allocation",{shelf : result}));
					                }
					            });
					        },
            'get_products' : function get_products(barcode){
                                allocations.call('get_json_products',[barcode]).then(function(result){
                                    if(result.result == 0){
                                        $('#result').html('');
                                        NotifyVibrate()
                                        NotifyPlay()
                                        if($('.error_msg').length){
                                            $('.error_msg').text(result.error);
                                        }else{
                                            $('#barcode-form').before(core.qweb.render("Error",{error : result.error}));
                                        }
                                    }else{
                                        $('.error_msg').remove();
                                        $('#result').html(core.qweb.render("block_allocation_shelf",{allocations : result}));
                                    }
                                });
                            },
            'get_new_allocation' : function get_new_allocation(barcode){
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
                                            $('#barcode-form').before(core.qweb.render("Error",{error : result.error}));
                                        }
                                    }else{
                                        $('.error_msg').remove();
                                        $('#barcode-form').detach();
                                        $('#back').attr('onclick','back("BARCODE PRODOTTO","get_new_allocation",this)');
                                        $('#back').attr('href','#');
                                        $('#result').before('<p id="sup_text">Scegli il ripiano da cui spostare la quantità desiderata</p>');
                                        $('#result').html(core.qweb.render("block_new_allocation",{shelf : result}));
                                    }
                                });
                            },
            'put_json_new_allocation' : function put_json_new_allocation(barcode){
                                qty = $('#qty').val()
                                pid = $('.prod_title').find('.block_title').attr('data-product');
                                wh_line_id = $('#barcode').attr('wh_line_id');
                                allocations.call('put_json_new_allocation',[barcode,qty,pid,wh_line_id]).then(function(result){
                                    $('.done_msg').remove();
                                    $('.orange_msg').remove();
                                    if(result.result == 0){
                                        NotifyVibrate()
                                        NotifyPlay()
                                        if($('.error_msg').length){
                                            $('.error_msg').text(result.error);
                                        }else{
                                            $('#sup_text').before(core.qweb.render("Error",{error : result.error}));
                                        }
                                        window.setTimeout(function() {window.scrollTo('.error_msg',{duration:'slow'});}, 0);
                                    }else{
                                            $('.error_msg').remove();
                                            $('#sup_text').remove();
                                            $('#result').html('');
                                            odoo_function['get_new_allocation'](result.product_barcode);
                                            $('#result').before('<div class="done_msg">PRODOTTO ALLOCATO</div>');
                                            window.setTimeout(function() {window.scrollTo('.done_msg',{duration:'slow'});}, 0);
                                    }
                                });
                            },
            'pick_up_barcode' : function pick_up_barcode(barcode){
                                $('.done_msg').remove();
                                $('.orange_msg').remove();
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
                                            products.push(value)
                                            $('#barcode').val(barcode)
                                        }
                                    }); 
                                }

                                if(products.length==0){
                                    NotifyVibrate()
                                    NotifyPlay()
                                    if($('.error_msg').length){
                                        $('.error_msg').text('Barcode non trovato nella lista');
                                    }else{
                                        $('#barcode-form').before(core.qweb.render("Error",{error : 'Barcode non trovato nella lista'}));
                                    }
                                    window.setTimeout(function() {window.scrollTo('.error_msg',{duration:'slow'});}, 0);
                                    $('#barcode').val('');
                                    $('#barcode').focus();
                                    return true;
                                }

                                if(products.length>1){
                                    var href = window.location.href;
                                    var wave_id = href.substr(href.lastIndexOf('/') + 1);
                                    wave_id = wave_id.replace(/\D/g,'');
                                    pid = $(products[0]).attr('data-pid');
                                    filter = [['picking_id.wave_id','=',parseInt(wave_id)],['product_id','=',parseInt(pid)]]
                                    new Model('stock.pack.operation').query().filter(filter).all().then(function(res){
                                        var qty_done = 0
                                        var qty_all = 0
                                        $(res).each(function(index,value){
                                            qty_done = qty_done + parseInt(value.qty_done)
                                            qty_all = qty_all +parseInt(value.product_qty)
                                        })
                                        if( qty_all == qty_done ){
                                            NotifyVibrate()
                                            NotifyBeep()
                                            if($('.error_msg').length){
                                                $('.error_msg').text('Prodotto già pickuppato da qualcun altro');
                                            }else{
                                                $('#barcode-form').before(core.qweb.render("Error",{error : 'Prodotto già pickuppato da qualcun altro'}));
                                            }
                                            $('#barcode').val('');
                                            $('#barcode').focus();
                                        }else{
                                            $('.error_msg').remove();
                                            if(qty_done > 0){
                                                $('#barcode-form').before(core.qweb.render("Error",{error : 'Attenzione: il prodotto è già stato pickuppato da una delle locazioni.'}));
                                            }
                                            NotifyVibrate()
                                            NotifyBeep()
                                            window.shelfs = new Array();
                                            var passing_shelfs = new Array();
                                            $(products).each(function(index,value){
                                                window.shelfs.push({'name' : $(value).attr('data-shelf'), 'id' :$(value).attr('data-shelf-id'),'qty':$(value).find('.qty_for_shelf').text() })
                                                passing_shelfs.push($(value).attr('data-shelf'));
                                            })
                                            NotifyMessage('Da quale ripiano vuoi scaricare il prodotto?',passing_shelfs,response_message)
                                            $('#barcode-form').before(core.qweb.render("shelfs_choice",{shelfs : window.shelfs, }));
                                            $('.shelf_pick').on('click',function(e){
                                                e.preventDefault();
                                                response_message($(this).attr('data-ids'));
                                            })
                                            window.setTimeout(function() {window.scrollTo('.error_msg',{duration:'slow'});}, 0);
                                            $('#barcode').val('');
                                            $('#barcode').focus();
                                            return true;
                                        }
                                    })
                                }

                                if(products.length==1){
                                    var href = window.location.href;
                                    var wave_id = href.substr(href.lastIndexOf('/') + 1);
                                    wave_id = wave_id.replace(/\D/g,'');
                                    pid = $(products).attr('data-pid');
                                    filter = [['picking_id.wave_id','=',parseInt(wave_id)],['product_id','=',parseInt(pid)]]
                                    new Model('stock.pack.operation').query().filter(filter).all().then(function(res){
                                        var qty_done = 0
                                        var qty_all = 0
                                        $(res).each(function(index,value){
                                            qty_done = qty_done + parseInt(value.qty_done)
                                            qty_all = qty_all +parseInt(value.product_qty)
                                        })
                                        if( qty_all == qty_done ){
                                            NotifyVibrate()
                                            NotifyBeep()
                                            if($('.error_msg').length){
                                                $('.error_msg').text('Prodotto già pickuppato da qualcun altro');
                                            }else{
                                                $('#barcode-form').before(core.qweb.render("Error",{error : 'Prodotto già pickuppato da qualcun altro'}));
                                            }
                                            $('#barcode').val('');
                                            $('#barcode').focus();
                                        }else{
                                            $('.error_msg').remove();
                                            window.shelfs = new Array();
                                            window.shelfs.push({'name' : $(products[0]).attr('data-shelf'), 'id' :$(products[0]).attr('data-shelf-id'),'qty':$(products[0]).find('.qty_for_shelf').text() })
                                            response_message(0);
                                        }
                                    })
                                }
                            },
            'set_pick_up' : function set_pick_up(wave_id,shelf_id,barcode,qty_to_down){

                                wave.call('wave_pick_ip',[barcode,shelf_id,wave_id,qty_to_down])
                                $('.product_row').each(function(index,value){
                                    if($(value).attr('data-barcode') == barcode && $(value).attr('data-shelf-id')==shelf_id){
                                        var classe = 'done_msg'
                                        if(parseInt(qty_to_down) > 1){
                                            classe = 'orange_msg'
                                        }
                                        var nome_ripiano = $(value).attr('data-shelf')
                                        $('#result').before('<div class="'+classe+'">Hai scaricato <b>'+qty_to_down+'</b> - '+$(value).find('.name_pid').text()+' da <b>'+nome_ripiano+'</b></div>');
                                        window.setTimeout(function() {window.scrollTo(value,{duration:0});}, 0);
                                        $(value).css('background-color','#87D37C').slideUp(1000);
                                        setTimeout(function() {
                                          $(value).remove();
                                        }, 1000);
                                        block = $(this).closest('.block').find('.product_row');
                                        if(block.length==1){
                                            $(this).closest('.block').slideUp(1000)
                                        }
                                        
                                        window.setTimeout(function() {window.scrollTo('.done_msg',{duration:'slow'});}, 0);
                                        $('#barcode').val('');
                                        $('#barcode').focus();
                                    }
                                });
                                
                            },
        }

        $('.open_image').on('click', function(e) {
            pid = $(e.currentTarget).attr('data-pid');
            new Model('product.product').query(['image']).filter([['id','=',pid]]).first().then(function(result){
                image_url = result.image
                html = '<image src="data:image/png;base64,'+image_url+'" width="300px" />'
                res = '<div id="image_product_popup" style="border:1px solid #6C7A89;margin-top:5px; padding:5px">'+html+'<a href="#" id="close_image" style="float:right;font-size:15px">X</a></div>';
                $(e.currentTarget).after(res)
                $('#close_image').on('click',function(e){
                    $('#image_product_popup').remove();
                    return false;
                })
                return false;
            });
            
        });
        

        $('#barcode-form').on('submit', function(e) {
           submitform(e);
        });

        $('#close_reverse').on('click', function(e) {
            var href = window.location.href;
            var wave_id = href.substr(href.lastIndexOf('/') + 1);
            new Model('stock.picking.wave').call('close_reverse',[wave_id]).then(function(e){
                $('#barcode-form').before('<div class="done_msg">LISTA CHIUSA</div>');
            })
        });

        window.back = function(title,func,elem){
            $('.error_msg').remove();
            $('#result').html('').before(core.qweb.render("barcode_form",{title : title,data_function: func}));
            $('#sup_text').remove();
            $('#barcode-form').on('submit', function(e) {
                submitform(e);
            });
            $(elem).removeAttr('onclick');
            return false;
        }

        window.select_shelf_to_move = function(alloc_line_id,elem,func){
            $('.modify').closest('.block').find('.block_content').remove();
            $('.modify').closest('.block').find('.block_title').removeClass('block_title modify').addClass('block_content');
            $(elem).find('.block_content').removeClass('block_content').addClass('block_title modify');
            $(elem).after('<div class="block_content modify"></div>');
            $(elem).closest('.block').find('.block_content').html(core.qweb.render('new_shelf_form',
                {qty_max:$(elem).find('.b_qty').text(),'data_function': 'put_json_new_allocation','wh_line_id' : alloc_line_id}));
            window.setTimeout(function() {window.scrollTo(elem.find('#barcode',{duration:'slow'}));}, 0);
            $('#barcode-form').on('submit', function(e) {
                submitform(e);
            });
        }

        
    });      

});