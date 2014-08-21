/*
    This file is responsible for actually executing or scheduling an execution of all other functions or plugins.
*/


var magnificPopup;


$(document).ready(function(){
    // Make threads in the board view (catalog) equal in height.
    equalizeHeight('#threads a');

    // Create relative dates.
    $('time.timeago').timeago();

    // Highlight code blocks.
    $('pre code').each(function(i, e){hljs.highlightBlock(e)});

    // Create tooltips when hovering over post links in a thread,
    $('#body-thread #posts').on('mouseenter', '.post-link', function(event){
        // Do not create tooltip again.
        if ("object" === typeof $(event.target).data('qtip')){
            return;
        }

        var postNumber = $(event.target).attr("post_id");
        addPostTooltip(event.target, postNumber);
    });

    // Smooth scrolling when clicked on a post link.
    $('body').on('click', '.post-link', function(event){
        var selector = $.attr(this, 'href');

        // Don't prevent the default beaviour on external links.
        if (selector.match(/^#post-[0-9]+$/) !== null){
            highlightPost(selector);
            goToAnchor(selector);
            window.history.pushState(null, null, selector);
            event.preventDefault();
        }
    });

    // Temporary highlight a post after loading a page with the #anchor in the link.
    if (window.location.hash){
        if (window.location.hash.match(/#post-[0-9]+/) !== null){
            highlightPost(window.location.hash);
        }
    }

    if ($("#body-thread").length){
        // Generate internal post links urls (>>1234).
        createPostLinks();

        // Save threads when the button is clicked.
        $('.post').on('click', '.button-save, .button-unsave', function(event){
            ajax_save(event.target);
        });

        // Add autocomplete to a 'new tag' input.
        if ($('#add-tag-input').length){
            $('#add-tag-input').autocomplete({
                serviceUrl: info_data.ajax_url_suggest_tag,
                minChars: 2
            });
        }

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

    // Additional event handling for the popup gallery link - it is necessary
    // to close the overlay before scrolling the page.
    $('body').on('click', '.gallery-post-link', function(event){
        $.magnificPopup.instance.close();
    });

    // Popup image gallery.
    magnificPopup = $('.post-image').magnificPopup({
        type:'image',
        gallery:{
            enabled: true,
            preload: [0, 1]
        },
        image:{
            titleSrc: function(item){
                var postId = item.el.closest('.post').attr('id');
                return '<a class="post-link gallery-post-link" href="#' + postId + '">&gt;&gt;' + postId.split("-")[1];  + '</a>';
            }
        }
    });
});
