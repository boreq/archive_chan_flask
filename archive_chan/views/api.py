import json

from django.db.models import Avg
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic.base import View

from archive_chan.models import Update, Image, Thread, Tag, TagToThread
import archive_chan.lib.stats as stats

class ApiError(Exception):
    def __init__(self, status_code=500, error_code='unknown', message='Unknown server error.'):
        self.status_code = status_code
        self.error_code = error_code
        super(ApiError, self).__init__(message)

class NotImplementedApiError(ApiError):
    def __init__(self, **kwargs):
        status_code = kwargs.get('status_code', 501)
        error_code = kwargs.get('error_code', 'not_implemented')
        message = kwargs.get('message', 'Not implemented.')
        super(NotImplementedApiError, self).__init__(status_code, error_code, message) 

class ApiView(View):
    def handle_exception(self, exception):
        """Extract exception parameters."""
        response_data = {
            'error_code': exception.error_code,
            'message': str(exception),
        }
        return (response_data, exception.status_code)

    def dispatch(self, request, *args, **kwargs):
        """Try to use the right method and handle the exceptions.
        This view will try to get the data from <method_name>_api_response().
        """
        try:
            attr_name = request.method.lower() + '_api_response'
            if request.method.lower() in self.http_method_names and hasattr(self, attr_name):
                response_data = getattr(self, attr_name)(request, *args, **kwargs)
                status_code = 200
            else:
                return self.http_method_not_allowed(request, *args, **kwargs)

        # Handle the exceptions thorown on purpose.
        except ApiError as e:
            response_data, status_code = self.handle_exception(e)

        # Handle other exceptions.
        except Exception as e:
            response_data, status_code = self.handle_exception(ApiError())

        return HttpResponse(
            json.dumps(response_data, indent=4),
            content_type='application/json',
            status=status_code
        )

class StatusView(ApiView):
    def get_chart_data(self, queryset):
        """Creates data structured as required by Google Charts."""
        chart_data = {
            'cols': [{'label': 'Date', 'type': 'datetime'}, {'label': 'Time per post', 'type': 'number'}],
            'rows': []
        }

        if queryset is None:
            return chart_data

        for entry in queryset:
            value_string = format("Date(%s, %s, %s, %s, %s, %s)" % (
                entry['date'].year,
                entry['date'].month - 1, # JavaScript months start at 0.
                entry['date'].day,
                0,
                0,
                0
            ))

            label_string = entry['date'].strftime('%Y-%m-%d')

            if entry['average_posts'] != 0:
                value = round(entry['average_time'] / entry['average_posts'], 3)
            else:
                value = 0

            chart_data['rows'].append({
                'c': [
                    {'v': value_string, 'f': label_string},
                    {'v': value},
                ]
            })

        return chart_data

    def get_api_response(self, request, *args, **kwargs):
        response_data = {}

        # Last updates.
        last_updates = Update.objects.order_by('board__name', '-start').distinct('board').select_related('board')

        response_data['last_updates'] = [{
            'board': str(update.board),
            'start': update.start.isoformat(),
            'end': update.end.isoformat() if update.end else None,
            'status': update.status,
            'status_verbose': update.get_status_display(),
        } for update in last_updates]

        # Chart data.
        updates = Update.objects.filter(status=Update.COMPLETED).extra({
            'date': 'date("end")'
        }).values('date').order_by('date').annotate(
            average_time=Avg('total_time'),
            average_posts=Avg('added_posts')
        )

        response_data['chart_data'] = self.get_chart_data(updates)

        return response_data

class StatsView(ApiView):
    def get_api_response(self, request, *args, **kwargs):
        board_name = request.GET.get('board', None)
        thread_number = request.GET.get('thread', None)
        return stats.get_stats(board=board_name, thread=thread_number)

class GalleryView(ApiView):
    def get_api_response(self, request, *args, **kwargs):
        board_name = request.GET.get('board')
        thread_number = request.GET.get('thread')
        last = request.GET.get('last')
        amount = int(request.GET.get('amount', 10))

        queryset = Image.objects.select_related('post', 'post__thread', 'post__thread__board')
        
        # Board specific gallery?
        if board_name is not None:
            queryset = queryset.filter(
                post__thread__board=board_name
            )

        # Thread specific gallery?
        if thread_number is not None:
            queryset = queryset.filter(
                post__thread__number=thread_number
            )

        # If this is not a first request we have to fetch those images which are not present in the gallery.
        if last is not None:
            queryset = queryset.filter(
                id__lt=last
            )

        queryset = queryset.order_by('-post__time')[:amount]

        # Prepare the data.
        json_data = {
            'images': []
        }

        for image in queryset:
            json_data['images'].append({
                'id': image.id,
                'board': image.post.thread.board.name,
                'thread': image.post.thread.number,
                'post': image.post.number,
                'extension': image.get_extension(),
                'url': image.image.url,
                'post_url': reverse(
                    'archive_chan:thread',
                    args=(image.post.thread.board.name, image.post.thread.number)
                ) + format('#post-%s' % image.post.number)
            })
        
        return json_data

def ajax_save_thread(request):
    """View used for AJAX save thread calls."""
    response = {}

    if request.user.is_staff:
        try:
            thread_number = int(request.POST['thread'])
            board_name = request.POST['board']
            state = request.POST['state']

            state = (state == 'true')

            thread = Thread.objects.get(board=board_name, number=thread_number)
            thread.saved = state
            thread.save()

            response = {
                'state': thread.saved
            }

        except:
            raise
            response = {
                'error': 'Error.'
            }
    else:
        response = {
            'error': 'Not authorized.'
        }

    return HttpResponse(json.dumps(response), content_type='application/json')

def ajax_get_parent_thread(request):
    """Returns a number of a thread the specified post belongs to."""
    response = {}

    try:
        post_number = int(request.GET['post'])
        board_name = request.GET['board']

        parent_thread_number = Post.objects.get(
            thread__board=board_name,
            number=post_number
        ).thread.number

        response = {
            'parent_thread': parent_thread_number
        }

    except:
        response = {
            'error': 'Error.'
        }

    return HttpResponse(json.dumps(response), content_type='application/json')

def ajax_suggest_tag(request):
    """View used for AJAX tag suggestions in the 'new tag' field in the thread view."""
    response = {}

    try:
        query = request.GET['query']

        tags = Tag.objects.filter(name__icontains=query)[:5]

        response = {
            'query': query, 
            'suggestions': [tag.name for tag in tags]
        }

    except:
        response = {
            'error': 'Error.'
        }

    return HttpResponse(json.dumps(response), content_type='application/json')

def ajax_add_tag(request):
    """View used for adding a tag to a thread."""
    response = {}

    if request.user.is_staff:
        try:
            thread_number = int(request.POST['thread'])
            board_name = request.POST['board']
            tag = request.POST['tag']

            exists = TagToThread.objects.filter(
                thread__number=thread_number, 
                thread__board__name=board_name,
                tag__name=tag
            ).exists()

            if not exists:
                thread = Thread.objects.get(number=thread_number, board__name=board_name)
                tag, created_new_tag = Tag.objects.get_or_create(name=tag)
                tag_to_thread = TagToThread(thread=thread, tag=tag)
                tag_to_thread.save()

                added = True
            else:
                added = False

            response = {
                'added': added
            }

        except:
            response = {
                'error': 'Error.'
            }
    else:
        response = {
            'error': 'Not authorized.'
        }

    return HttpResponse(json.dumps(response), content_type='application/json')

def ajax_remove_tag(request):
    """View used to remove a tag related to a thread."""
    response = {}

    if request.user.is_staff:
        try:
            thread_number = int(request.POST['thread'])
            board_name = request.POST['board']
            tag = request.POST['tag']

            TagToThread.objects.get(
                thread__number=thread_number, 
                thread__board__name=board_name,
                tag__name=tag
            ).delete()

            response = {
                'removed': True
            }

        except:
           response = {
                'error': 'Error.'
            }
    else:
        response = {
            'error': 'Not authorized.'
        }

    return HttpResponse(json.dumps(response), content_type='application/json')
