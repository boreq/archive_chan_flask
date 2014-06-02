$(function(){
    // Nice grid.
    var $container = $('#gallery-images');
    $container.imagesLoaded(function(){
        $container.masonry({
            itemSelector : 'li'
        });
    });

    // Popup image gallery.
    magnificPopup = $('.gallery-image').magnificPopup({
        type:'image',
        gallery:{
            enabled: true,
            preload: [0, 1]
        },
        image:{
            titleSrc: function(item){
                var par = item.el.closest('li');
                var link = $(par).find('.post-link');
                return '<a class="post-link gallery-post-link" href="' + link.attr('href') + '">&gt;&gt;/' + $(par).attr('board')  + '/' + $(par).attr('post')  + '</a>';
            }
        }
    });
});
