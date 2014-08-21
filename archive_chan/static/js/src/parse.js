/*
    Functions which dynamically generate elements like post links.
*/


// Easily create an object which holds post properties.
function createPostObject(element, number, board){
    return {
        element: element,
        number: number,
        id: '#post-' + number,
        board: board
    }
}


// Create a post object from a post jQuery object.
function createParentPostObject(element){
    var number = element.attr('id').split('-')[1];
    var board = info_data.board_name;
    return createPostObject(element, number, board);
}


// Create a post object from a post link jQuery object.
function createTargetPostObject(link){
    var number = $(link).attr('post_id');
    var element = $('#post-' + number);
    var board = null;
    // Get board name from the link attribute or use the current board if
    // attribute does not exist.
    if ($(link).attr('post_board') !== undefined)
        board = $(link).attr('post_board');
    else
        board = info_data.board_name;
    return createPostObject(element, number, board);
}


// Call this on load to generate links and backlinks to the comments in the
// thread view.
function createPostLinks(){
    $('#posts .post-link').each(function(index, element){
        var ownerPost = createParentPostObject($(element).closest('#posts>li'));
        var linkedPost = createTargetPostObject(element);

        if (linkedPost.element.length){
            // Post exists on this page.
            addBacklink(ownerPost, linkedPost);
            $(element).attr('href', linkedPost.id);
        }else{
            // It is necessary to create a link to different thread.
            $.ajax({
                url: info_data.ajax_url_get_parent_thread,
                data: {
                    post: linkedPost.number,
                    board: linkedPost.board
                },
                type: 'GET',
                cache: true
            }).done(function(response){
                // Success! Construct the link using the known url and put it
                // in the href attribute of the post link.
                link = info_data.thread_url.replace('/' + info_data.board_name + '/',
                                                    '/' + linkedPost.board + '/');
                link = link.replace(info_data.thread_number,
                                    response['parent_thread']);
                $(element).attr('href', link + linkedPost.id);
            }).fail(function(jqXHR){
                // Failed! Mark link dead.
                $(element).removeAttr('href');
                $(element).addClass('post-link-dead');

                // In case of a real error (not normal API behaviour) add
                // the information that the data could not be downloaded.
                var responseText = $.parseJSON(jqXHR.responseText);
                if (jqXHR.status !== 404 && responseText.error_code !== 'not_found'){
                    $(element).append(' <i class="fa fa-question"></i>');
                    $(element).attr('title', 'Post does not exist in this thread. Could not download the data to create a link.');
                }
            });
        }
    });
}


// Add backlink to the post header.
// Accepts post objects.
function addBacklink(sourcePostObject, targetPostObject){
    // Find list.
    var backlinks = $(targetPostObject.element).find('.post-backlinks');

    // Create list if necessary.
    if (!$(backlinks).length){
        $(targetPostObject.element).find('.post-header')
                                   .append('<ul class="post-backlinks"></ul>');
        var backlinks = $(targetPostObject.element).find('.post-backlinks');
    }

    // Check if there is no such backlink.
    if (!$(backlinks).find("[href='" + sourcePostObject.id + "']").length){

        // Create backlink.
        $(backlinks).append('<li><a href="' + sourcePostObject.id+ '" post_id="' + sourcePostObject.number + '" class="post-link">&gt;&gt;' + sourcePostObject.number + '</a></li>');
    }
}


// Adds tooltip to the link. Should be called on hover rather than on link
// creation. That way the preview will contain all backlinks.
function addPostTooltip(target, postNumber){
    var sourcePost = $('#post-' + postNumber);

    if (!sourcePost.length){
        return;
    }

    $(target).qtip({
        content: {
            text: '<div class="post">' + sourcePost.html() + '</div>'
        },
        position: {
            my: 'left center',
            at: 'right center',
            adjust: {
                method: 'flip invert'
            },
            viewport: $(window)
        },
        show: {
            ready: true,
            delay: 0
        },
        hide: {
            delay: 0
        }
    });
}


// Highlights the specified post (for example after clicking on an anchor).
function highlightPost(selector){
    $(selector).addClass('post-highlight');

    var delay = setTimeout(function(){
        $(selector).removeClass('post-highlight')
    }, 2000);
}
