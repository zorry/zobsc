$(document).ready(function() {
    var pathname = window.location.pathname.split( '/' )[1];
    if (pathname!=''){
        var lis = $('ul.nav').children('li');
        lis.removeClass('active');
        $('ul.nav').children('#'+pathname).addClass('active');
    }
    
});