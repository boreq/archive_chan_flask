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
