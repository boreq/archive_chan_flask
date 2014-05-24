/* This file is responsible for actually executing or scheduling an execution of all other functions or plugins.
*/

$(document).ready(function(){
    // Make threads in the board view (catalog) equal in height.
    equalizeHeight('#threads .img-container');
    equalizeHeight('#threads a');

    // Finish comments in a thread view with three dots...
    $('#threads .thread-comment').dotdotdot({
        wrap: 'letter'
    });

    // Generate internal post links urls (>>1234).
    createPostLinks();

    // Create relative dates.
    $('time.timeago').timeago();

    // Highlight code blocks.
    $('pre code').each(function(i, e){hljs.highlightBlock(e)});

    // Create tooltips when hovering over post links in a thread,
    $('#posts').on('mouseenter', '.post-link', function(event){
        // Do not create tooltip again.
        if ("object" === typeof $(event.target).data('qtip')){
            return;
        }

        var postId = $(event.target).attr("post_id");
        addPostTooltip(event.target, postId);
    });

    // Temporary higlight a post after clicking on a local link (within the same thread).
    $('#posts').on('click', '.post-link', function(event){
        var postId = $(event.target).attr("post_id");
        var selector = '#post-' + postId;
        higlightPost(selector);
    });

    // Temporary higlight a post after loading a page with the #anchor in the link.
    if (window.location.hash){
        if (window.location.hash.match(/#post-[0-9]+/) !== null){
            higlightPost(window.location.hash);
        }
    }

    if ($("#body-thread").length){
        // Save threads when the button is clicked.
        $('.post').on('click', '.button-save, .button-unsave', function(event){
            ajax_save(event.target);
        });

        // Add autocomplete to a 'new tag' input.
        $('#add-tag-input').autocomplete({
            serviceUrl: info_data.ajax_url_suggest_tag,
            minChars: 2
        });

        // Add a tag to a thread after user presses enter in an input.
        $('.post').on('keypress', '#add-tag-input', function(event){
            if (event.which == 13){
                ajax_add_tag(event.target);
            }
        });

        // Remove tag after user clicks a button.
        $('.post').on('click', '.remove-tag', function(event){
            ajax_remove_tag(event.target);
        });
    }
});

