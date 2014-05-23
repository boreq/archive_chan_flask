function ajax_save(clicked_button){
    state = $(clicked_button).hasClass('button-save');
    
    $.ajax({
        url: info_data.ajax_url_save,
        data: {
            thread: info_data.thread_number, // Those are set in the template to make things easier.
            board: info_data.board_name,
            state: state
        },
        type: 'GET',
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

function ajax_add_tag(input){
    if (input.value.length <= 0){
        return;
    }

    $.ajax({
        url: info_data.ajax_url_add_tag,
        data: {
            thread: info_data.thread_number, // Those are set in the template to make things easier.
            board: info_data.board_name,
            tag: input.value
        },
        type: 'GET',
        cache: false
    }).done(function(response){
        if (response['error']){
            alert(response['error']);
        }else{
            if (response['added']){
                $('.tags').append('<li><i class="fa fa-fw fa-tag" title="Tag added by the user"></i><a class="tag-link" href="' + info_data.board_url + '?tag=' + input.value + '">' + input.value + '</a><a class="remove-tag" title="Remove the tag"><i class="fa fa-times"></i></a></li>');
            }
        }
    });
    
}

function ajax_remove_tag(sender){
    $.ajax({
        url: info_data.ajax_url_remove_tag,
        data: {
            thread: info_data.thread_number, // Those are set in the template to make things easier.
            board: info_data.board_name,
            tag: $(sender).closest('li').find('.tag-link').text()
        },
        type: 'GET',
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
