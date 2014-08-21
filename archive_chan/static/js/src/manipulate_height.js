/*
    Functions which are used to change the height of various page elements.
*/


// Sets the height of all matched elements to the height of the highest of
// those elements.
function equalizeHeight(selector){
    var maxHeight = 0;
    $(selector).each(function(){
        var height = $(this).height();
        if (height > maxHeight)
            maxHeight = height;
    });
    $(selector).height(maxHeight);
}
