/* This file contains functions which  dynamically generate elements like post links.
*/

// Call this on load to generate links to the comments in the thread view (>>1234).
function createPostLinks(){
    $('.post-link').each(function(index, element){
        var ownerPost = $(element).closest("#posts>li");
        var ownerPostId = $(ownerPost).attr("id").split("-")[1];

        var linkedPostId = $(element).attr("post_id");
        var linkedPost = '#post-' + linkedPostId;
        var linkedPostBoard = ($(element).attr("post_board") !== undefined ? $(element).attr("post_board") : info_data.board_name);

        if ($(linkedPost).length){ // Post exists on this page.
            addBacklink(linkedPost, ownerPostId);
            $(element).attr('href', '#post-' + linkedPostId);
        }
        else{ // It is necessary to create a link to different page.
            $.ajax({
                url: info_data.ajax_url_get_parent_thread,
                data: {
                    post: linkedPostId,
                    board: linkedPostBoard
                },
                type: 'GET',
                cache: true
            }).done(function(response){
                if (response['error']){
                    $(element).removeAttr('href');
                    $(element).addClass('post-link-dead');
                }else{
                    link = info_data.thread_url.replace('/' + info_data.board_name + '/', '/' + linkedPostBoard + '/')
                    link = link.replace(info_data.thread_number, response['parent_thread']);
                    $(element).attr('href', link + '#post-' + linkedPostId);
                }
            });
        }
    });
}

// Add backlink to the post header.
// selector toPost, int backlinkTarget
function addBacklink(toPost, backlinkTarget){
    var backlinks = $(toPost).find('.post-backlinks');

    // Create list if necessary.
    if (!$(backlinks).length){
        $(toPost).find(".post-header").append('<ul class="post-backlinks"></ul>');
        var backlinks = $(toPost).find('.post-backlinks');
    }

    // Check if there is no such backlink.
    if (!$(backlinks).find("[href='#post-" + backlinkTarget + "']").length){

        // Create backlink.
        $(backlinks).append('<li><a href="#post-' + backlinkTarget + '" post_id="' + backlinkTarget + '" class="post-link">&gt;&gt;' + backlinkTarget + '</a></li>');
    }
}

// Adds tooltip to the link. Should be called on hover rather than on link creation. That way the preview will contain backlinks which are created later.
function addPostTooltip(element, postId){
    var sourcePost = '#post-' + postId;

    if (!$(sourcePost).length){
        return;
    }

    $(element).qtip({
        content: {
            text: '<div class="post">' + $(sourcePost).html() + '</div>'
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

// Highlights the specified post (for example after clicking an anchor linking to it).
function higlightPost(selector){
    $(selector).addClass('post-highlight');

    var delay = setTimeout(function(){
        $(selector).removeClass('post-highlight')
    }, 2000);
}
