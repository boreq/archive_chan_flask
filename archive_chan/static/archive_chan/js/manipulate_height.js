/* This script contains functions which assist with manipulating height of various page elements.
Unfortunately those can't be solved with CSS.
*/

// Sets the height of all matched elements to the height of the highest of those elements.
function equalizeHeight(selector){
    var maxHeight = 0;

    $(selector).each(function(){
       if ($(this).height() > maxHeight){
           maxHeight = $(this).height();
       }
    });

    $(selector).height(maxHeight);
}

// Ensures that the specified element's bottom border isn't below its parent's bottom border.
function limitHeight(selector){
    $(selector).each(function(){
        var parentHeight = $(this).parent().height();
        var parentOuterHeight = $(this).parent().outerHeight();

        var parentOffset = $(this).parent().offset().top;
        var thisOffset = $(this).offset().top;

        $(this).height(parentHeight - (thisOffset - parentOffset) + ((parentOuterHeight - parentHeight) / 2));
    });
}
