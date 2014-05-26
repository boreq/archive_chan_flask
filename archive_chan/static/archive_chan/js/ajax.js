/* This file contains functions called in order to asynchronously modify the website.
*/

// Function saving the thread.
// Executed when user clicks the save thread button.
function ajax_save(clicked_button){
    // Decide if the code should request saving or unsaving the thread.
    state = $(clicked_button).hasClass('button-save');

    $.ajax({
        url: info_data.ajax_url_save,
        beforeSend: function (request){
            request.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
        },
        data: {
            thread: info_data.thread_number, // Those are set in the template 
            board: info_data.board_name,     // to make things easier.
            state: state
        },
        type: 'POST',
        cache: false
    }).done(function(response){
        if (response['error']){
            alert(response['error']);
        }else{
            if (response.state){
                $(clicked_button).removeClass('button-green button-save');
                $(clicked_button).addClass('button-red button-unsave');
                $(clicked_button).text("Unsave thread");
            }else{
                $(clicked_button).removeClass('button-red button-unsave');
                $(clicked_button).addClass('button-green button-save');
                $(clicked_button).text("Save thread");
            }
        }
    });
}

// Function adding a tag to a thread.
// Executed when user presses enter in the add tag input.
function ajax_add_tag(input){
    // Input was empty, abort.
    if (input.value.length <= 0){
        return;
    }

    $.ajax({
        url: info_data.ajax_url_add_tag,
        beforeSend: function (request){
            request.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
        },
        data: {
            thread: info_data.thread_number, // Those are set in the template
            board: info_data.board_name,     // to make things easier.
            tag: input.value
        },
        type: 'POST',
        cache: false
    }).done(function(response){
        if (response['error']){
            alert(response['error']);
        }else{
            if (response['added']){
                $('.tags').append('<li><i class="fa fa-fw fa-tag" title="Tag added by the user"></i><a class="tag-link" href="' + info_data.board_url + '?tag=' + input.value + '">' + input.value + '</a><a class="remove-tag" title="Remove the tag"><i class="fa fa-times"></i></a></li>'); // :(
            }
        }
    });
    
}

// Function removing a tag assigned to a thread.
// Executed when user clicks remove tag button.
function ajax_remove_tag(sender){
    $.ajax({
        url: info_data.ajax_url_remove_tag,
        beforeSend: function (request){
            request.setRequestHeader('X-CSRFToken', $.cookie('csrftoken'));
        },
        data: {
            thread: info_data.thread_number, // Those are set in the template
            board: info_data.board_name,     // to make things easier.
            tag: $(sender).closest('li').find('.tag-link').text()
        },
        type: 'POST',
        cache: false
    }).done(function(response){
        if (response['error']){
            alert(response['error']);
        }else{
            if (response['removed']){
                $(sender).closest('li').remove();
            }
        }
    });
}
