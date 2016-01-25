$(document).ready( function(){
	$('.top_menu').click(function(){
		if ($('#slide_menu').width() > 1){
			$("#slide_menu").animate({width: '0'});
		}else{
			$("#slide_menu").animate({width: '50%'});
		}
		
		return false;
	});
})
	
