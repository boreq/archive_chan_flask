function goToAnchor(anchor){
    $('html, body').animate({
        scrollTop: $(anchor).offset().top
    }, 600);
}
