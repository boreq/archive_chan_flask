$(function(){
    // Get first images.
    getImages();

    // Detect scrolling.
    $(window).scroll(function(){ 
        var windowBottom = $(window).scrollTop() + $(window).height();
        var listBottom = $("#gallery-images").offset().top + $("#gallery-images").outerHeight();

        // Fetch more images if user is getting close to the bottom of the list.
        if (windowBottom > listBottom - 500){
            getImages();
        }
    });
});


var lastImage = null, update = false, end = false;

// Init popup image gallery.
function popup(){
    magnificPopup = $('.gallery-image').magnificPopup({
        type: 'image',
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
}

// Main update function.
function getImages(){
    // Do not update if another update has not been completed yet or there are no more items to fetch.
    if (update || end){
        return;
    }

    update = true;

    request_data = {}

    if (info_data.thread)
        request_data['thread'] = info_data.thread;

    if (info_data.board)
        request_data['board'] = info_data.board;

    if (lastImage)
        request_data['last'] = lastImage;

    $.ajax({
        url: info_data.ajax_url_gallery,
        data: request_data,
        type: 'GET',
        cache: true
    }).done(function(response){
        if (response['error']){
            alert(response['error']);
            update = false;
        }else{
            addImages(response);
        }
    }).fail(function(){
        update = false;
    });
}

// This functions appends new images to the list.
function addImages(response){
    var arrayLength = response.images.length, images = '';

    // Received an empty list, that means that there is nothing to download.
    // Updates might be disabled now.
    if (arrayLength == 0){
        $('#gallery-images').after('<p class="gallery-end">No more images to load.</p>')
        end = true;
        return;
    }

    for(var i = 0; i < arrayLength; i++){
        var image = response.images[i];

        images += createImage(image);

        // Store the lowest received id.
        if (lastImage !== null){
            lastImage = Math.min(image.id, lastImage);
        }else{
            lastImage = image.id;
        }
    }

    images = $(images)

    if ("object" === typeof $('#gallery-images').data('masonry')){
        // Update.
        $('#gallery-images').append(images).imagesLoaded(function(){
            $('#gallery-images').masonry('appended', images);
            popup();
            update = false;
        });
    }else{
        // Initialize.
        $('#gallery-images').append(images).imagesLoaded(function(){
            var $container = $('#gallery-images');
            $container.masonry({
                itemSelector : 'li'
            });
            popup();
            update = false;
        });
    }
}

// Helper function creating html.
function createImage(image){
    var imageHtml;
    if (image.video){
        imageHtml = '<video src="' + image.url + '" controls></video>';
    }else{
        imageHtml = '<a class="gallery-image" href="' + image.url + '"><img src="' + image.url + '"></a>';
    }

    return '<li board="' + image.board + '" post="' + image.post  + '"><div>' + imageHtml + '<a class="post-link" href="' + image.post_url  + '">&gt;&gt;/' + image.board + '/' + image.post + '</a></div></li>';
}
