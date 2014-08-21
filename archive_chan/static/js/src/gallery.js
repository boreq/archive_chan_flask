/*
    Script which creates an infinite scroll effect on the gallery page.
*/


var resizeTimeout;
var container = '#gallery-images';
var lastImage = null, update = false, end = false;


$(function(){
    // Get first set of images.
    getImages();

    // Detect scrolling.
    $(window).scroll(function(){ 
        updateIfNeeded();
    });

    // Reposiiton masonry on window resize event.
    $(window).on('resize', function(){
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(repositionMasonry, 200);
    });
});


function repositionMasonry(){
    if ("object" === typeof $(container).data('masonry')){
        $(container).masonry();
    }
}


// Check if more content should be loaded and trigger the update function if
// necessary.
function updateIfNeeded(){
    var windowBottom = $(window).scrollTop() + $(window).height();
    var listBottom = $(container).offset().top + $(container).outerHeight();

    // Fetch more images if user is getting close to the bottom of the list.
    if (windowBottom > listBottom - 500){
        getImages();
    }
}


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
    // Do not update if another update has not been completed yet or there
    // are no more items to fetch.
    if (update || end)
        return;
    updateStart();
    request_data = {}

    if (info_data.thread)
        request_data['thread'] = info_data.thread;

    if (info_data.board)
        request_data['board'] = info_data.board;

    if (lastImage){
        request_data['last'] = lastImage;
        request_data['amount'] = 10;
    }else{
        request_data['amount'] = 20;
    }

    $.ajax({
        url: info_data.api_url,
        data: request_data,
        type: 'GET',
        cache: false
    }).done(function(response){
        addImages(response);
    }).fail(function(jqXHR){
        updateEnd();
        var responseText = $.parseJSON(jqXHR.responseText);
        if (response['message'])
            alert(response['message']);
    });
}


function updateStart(){
    update = true;
    $(container).after('<p class="gallery-throbber"><i class="fa fa-spinner fa-spin"></i></p>');
}


function updateEnd(){
    update = false;
    $('.gallery-throbber').remove();
    if (end)
        $(container).after('<p class="gallery-end"><i class="fa fa-circle-o"></i></p>')
}


// This functions appends new images to the list.
function addImages(response){
    var arrayLength = response.images.length, images = '';

    // List is not full, further updates might be disabled now.
    if (arrayLength < 10)
        end = true;

    // Received an empty list, that means that there are no more images
    // to download.
    if (arrayLength == 0){
        updateEnd();
        end = true;
        return;
    }

    for(var i = 0; i < arrayLength; i++){
        var image = response.images[i];

        images += createImage(image);

        // Store the lowest received id.
        if (lastImage !== null)
            lastImage = Math.min(image.id, lastImage);
        else
            lastImage = image.id;
    }

    images = $(images)

    if ("object" === typeof $(container).data('masonry')){
        // Update.
        $(container).append(images).imagesLoaded(function(){
            $(container).masonry('appended', images);
            $(container + ' li').show();
            popup();
            updateEnd();
            updateIfNeeded();
        });
    }else{
        // Initialize.
        $(container).append(images).imagesLoaded(function(){
            $(container).masonry({
                itemSelector: 'li'
            });
            $(container + ' li').show();
            popup();
            updateEnd();
            updateIfNeeded();
        });
    }
}


// Helper function creating html.
function createImage(image){
    var imageHtml;
    if (image.extension == '.webm'){
        imageHtml = '<video src="' + image.image_url + '" controls></video>';
    }else{
        imageHtml = '<a class="gallery-image" href="' + image.image_url + '"><img src="' + image.image_url + '"></a>';
    }

    return '<li style="display: none" board="' + image.board + '" post="' + image.post  + '"><div>' + imageHtml + '<a class="post-link" href="' + image.post_url  + '">&gt;&gt;/' + image.board + '/' + image.post + '</a></div></li>';
}
