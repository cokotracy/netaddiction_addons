window.BarcodeData = function(barcode) {
	barcode = $('#barcode').val(barcode);
	$('#barcode-form').trigger('submit');
};

window.submitform = function(e){
    if(e != ''){
         e.preventDefault();
    }
   
    barcode = $('#barcode').val();
    func = $('#barcode').attr('data-function');
    odoo_function[func](barcode)
}


$(document).ready(function(){
    odoo.define('netaddiction_warehouse', function (require) {
        var utils = require('web.utils');
        var Model = require('web.Model');
        var core = require('web.core');
        core.qweb.add_template("/netaddiction_warehouse/static/src/xml/search.xml");
        core.qweb.add_template("/netaddiction_warehouse/static/src/xml/allocation.xml");
        // do things with utils and Model
        var product = new Model('product.product');
        var allocations = new Model('netaddiction.wh.locations.line');

        odoo_function ={
        	'get_allocation': function get_allocation(barcode){
					            product.call('get_json_allocation',[barcode]).then(function(result){
					                if(result.result == 0){
					                    if($('.error_msg').length){
					                        $('.error_msg').text(result.error);
					                    }else{
					                        $('#result').html(core.qweb.render("Error",{error : result.error}));
					                    }
					                }else{
					                    $('#result').html(core.qweb.render("block_allocation",{shelf : result}));
					                }
					            });
					        },
            'get_products' : function get_products(barcode){
                                allocations.call('get_json_products',[barcode]).then(function(result){
                                    if(result.result == 0){
                                        if($('.error_msg').length){
                                            $('.error_msg').text(result.error);
                                        }else{
                                            $('#result').html(core.qweb.render("Error",{error : result.error}));
                                        }
                                    }else{
                                        $('#result').html(core.qweb.render("block_allocation_shelf",{allocations : result}));
                                    }
                                });
                            },
            'get_new_allocation' : function get_new_allocation(barcode){
                                product.call('get_json_allocation',[barcode]).then(function(result){
                                    if(result.result == 0){
                                        if($('.error_msg').length){
                                            $('.error_msg').text(result.error);
                                        }else{
                                            $('#result').html(core.qweb.render("Error",{error : result.error}));
                                        }
                                    }else{
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
                                    if(result.result == 0){
                                        if($('.error_msg').length){
                                            $('.error_msg').text(result.error);
                                        }else{
                                            $('#result').before(core.qweb.render("Error",{error : result.error}));
                                        }
                                    }else{
                                            $('.error_msg').remove();
                                            $('#sup_text').remove();
                                            $('#result').html('');
                                            odoo_function['get_new_allocation'](result.product_barcode);
                                            $('#result').before('<div class="done_msg">PRODOTTO ALLOCATO</div>');
                                    }
                                });
                            },
        }
        

        $('#barcode-form').on('submit', function(e) {
           submitform(e);
        });

        window.back = function(title,func,elem){
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
            $(document).scrollTop( $(elem).offset().top); 
            $('#barcode-form').on('submit', function(e) {
                submitform(e);
            });
        }

        
    });      

});