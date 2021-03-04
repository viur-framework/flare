jQuery(document).ready(function() {


	// jQuery('pre').each(function(i, block) {
  //   hljs.highlightBlock(block);
	// });

	jQuery('#fcside').click(function () {
		jQuery("body").css({ overflow: 'inherit' });
		jQuery(".sphinxsidebarwrapper").fadeOut(100);
		jQuery("#fcside").fadeOut(100);
	});

	jQuery.fn.autoScoll= function(activate){
		if (jQuery.isNumeric(activate) || activate==true){
			var offset = 0
			if (jQuery.isNumeric(activate)){
				offset = activate
			}
			jQuery(this.selector+" a[href^='#']").click(function(event){

				normalscroll=true;
				event.preventDefault();
				var place = jQuery(jQuery(this).attr('href'))
				if(!(place && place.offset() && place.offset().top)){
					return
				}
				jQuery('html,body').clearQueue()
				jQuery('html,body').stop()
				if(activate==true){
					offset =jQuery(window).height()/2-place.parent("div").height()/2
				}
				jQuery('html,body').animate({
					scrollTop: place.offset().top - offset + 20 //auf Nullinie Scrollen
				},1000,
					function(){
					setTimeout(function(){normalscroll=false},500);
					}
				);
			})
		}
	};

	jQuery("body").autoScoll(100);
});






var thescroll=0;
var scrolling =false;

function scrolleventhandler (e) {

	if( thescroll > jQuery(window).scrollTop()){
		scrolldir=-1;
	}else{
		scrolldir=1;
	}
	thescroll=jQuery(window).scrollTop();
	wh=parseInt(jQuery("body").css("height").replace("px", ""))

	if (scrolldir>0 || jQuery(window).scrollTop()>50) {
		jQuery('.logo').addClass("is-scrolled");
		jQuery('.is2').addClass("is-scrolled2");
		jQuery('.is3').addClass("is-scrolled3");
		jQuery('.is4').addClass("is-scrolled4");
		jQuery('.is5').addClass("is-scrolled5");
		jQuery('.viur').addClass("is-scrolled6");
		jQuery('.sphinxsidebarwrapper').addClass("is-scrolled7");

	} else {
		jQuery('.logo').removeClass("is-scrolled");
		jQuery('.is2').removeClass("is-scrolled2");
		jQuery('.is3').removeClass("is-scrolled3");
		jQuery('.is4').removeClass("is-scrolled4");
		jQuery('.is5').removeClass("is-scrolled5");
		jQuery('.viur').removeClass("is-scrolled6");
		jQuery('.sphinxsidebarwrapper').removeClass("is-scrolled7");

	}

}

jQuery(window).scroll(scrolleventhandler);
jQuery(window).resize(scrolleventhandler);







// ######################### COOKIES !!! ################################
function setCookie(key, value) {
	var expires = new Date();
	expires.setTime(expires.getTime() + (30 * 24 * 60 * 60 * 1000)) //30 Tage
	document.cookie = key + '=' + value + ';expires=' + expires.toUTCString() + ";path=/";
}

function getCookie(key) {
	var keyValue = document.cookie.match('(^|;) ?' + key + '=([^;]*)(;|$)');
	return keyValue ? keyValue[2] : null;
}

$(document).ready(function () {
	if (!getCookie("cookies-allowed")) {
		$(".cookie-info").addClass("is-active")
	}
	$(".cookie-info .js-cookieaction").on("click", function () {
		setCookie("cookies-allowed", "yes")
		$(".cookie-info").removeClass("is-active")
	})
});
// ##########