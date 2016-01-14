$(document).ready( function(){

		Device = new ScannerDevice({
				barcodeData: function (data, type){
					if($('#barcode').length){
						$('#barcode').val(data);
						if( $('#barcode').val().length>0){
							$('#auto_form').submit();
						}
					}else{
						$('input:focus').val(data);
						$('input:focus').closest('form').submit();
					}
					
				}
		});


		ScannerDevice.registerListener(Device);


});
