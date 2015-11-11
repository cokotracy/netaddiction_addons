$(document).ready( function(){

		Device = new ScannerDevice({
				barcodeData: function (data, type){
					$('#barcode').val(data);
					if( $('#barcode').val().length>0){
						$('#first_barcode').submit();
					}
				}
		});


		ScannerDevice.registerListener(Device);


});
