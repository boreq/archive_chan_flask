$(function(){
    var $container = $('#gallery-images');
    $container.imagesLoaded(function(){
        $container.masonry({
            itemSelector : '.gallery-image-container'
        });
    });
});
