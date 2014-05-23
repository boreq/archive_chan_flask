function equalizeHeight(selector){
    var maxHeight = 0;

    $(selector).each(function(){
       if ($(this).height() > maxHeight){
           maxHeight = $(this).height();
       }
    });

    $(selector).height(maxHeight);
}

function limitHeight(selector){
    $(selector).each(function(){
        var parentHeight = $(this).parent().height();
        var parentOuterHeight = $(this).parent().outerHeight();

        var parentOffset = $(this).parent().offset().top;
        var thisOffset = $(this).offset().top;

        $(this).height(parentHeight - (thisOffset - parentOffset) + ((parentOuterHeight - parentHeight) / 2));
    });
}
