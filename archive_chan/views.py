import json, datetime

from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.http import HttpResponse
from django.utils.timezone import utc
from django.db.models import Max, Min, Count
from django.views.generic import ListView

from archive_chan.models import Board, Thread, Post, Tag, TagToThread


class IndexView(ListView):
    """View showing all boards."""
    model = Board
    context_object_name = 'board_list'
    template_name = 'archive_chan/index.html'

    def get_queryset(self):
        return Board.objects.order_by('name')

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['body_id'] = 'body-home'
        return context


class BoardView(ListView):
    """View showing all threads in a specified board."""
    model = Thread
    context_object_name = 'thread_list'
    template_name = 'archive_chan/board.html'
    paginate_by = 20

    available_parameters = {
        'sort': (
            ('last_reply', 'Last reply'),
            ('creation_date', 'Creation date'),
            ('replies', 'Replies'),
        ),
        'saved': (
            ('all', 'All'),
            ('yes', 'Yes'),
            ('no',  'No'),
        ),
        'last_reply': (
            ('always', 'Always'),
            ('quarter', '15 minutes'),
            ('hour', 'Hour'),
            ('day', 'Day'),
            ('week', 'Week'),
            ('month', 'Month'),
        ),
        'tagged': (
            ('all', 'All'),
            ('yes', 'Yes'),
            ('auto', 'Automatically'),
            ('user', 'Manually'),
            ('no', 'No'),
        )
    }

    # Used to quickly translate text to a value. [hours]
    last_reply_times = {
        'quarter': 0.25,
        'hour': 1,
        'day': 24,
        'week': 24 * 7,
        'month': 24 * 30,
    }

    def get_parameters(self):
        """Extracts parameters related to filtering and sorting from a request object."""
        parameters = {}

        parameters['sort'] = self.request.GET.get('sort', None)
        parameters['sort_reverse'] = True

        # Reverse sorting?
        if not parameters['sort'] is None:
            parameters['sort_reverse'] = parameters['sort'].startswith("-")
            parameters['sort'] = parameters['sort'].strip('-')

        # Default sorting.
        if not parameters['sort'] in dict(self.available_parameters['sort']):
            parameters['sort'] = 'last_reply'
            parameters['sort_reverse'] = True

        # This makes template rendering easier - it is possible to just display this value directly.
        parameters['sort_with_operator'] = '-' + parameters['sort'] if parameters['sort_reverse'] else parameters['sort']

        # Default saved filter.
        parameters['saved'] = self.request.GET.get('saved', None)
        if not parameters['saved'] in dict(self.available_parameters['saved']):
            parameters['saved'] = 'all'

        # Default last reply.
        parameters['last_reply'] = self.request.GET.get('last_reply', None)
        if not parameters['last_reply'] in dict(self.available_parameters['last_reply']):
            parameters['last_reply'] = 'always'

        # Default tagged.
        parameters['tagged'] = self.request.GET.get('tagged', None)
        if not parameters['tagged'] in dict(self.available_parameters['tagged']):
            parameters['tagged'] = 'all'

        # Tags.
        parameters['tag'] = self.request.GET.get('tag', None)
        if parameters['tag'] is not None:
            parameters['tag'] = parameters['tag'].split()

        return parameters

    def filter_saved(self, queryset):
        """Apply requested filter to the queryset."""
        # Saved.
        if self.parameters['saved'] == 'yes':
            queryset = queryset.filter(saved=True)

        if self.parameters['saved'] == 'no':
            queryset = queryset.filter(saved=False)

        return queryset

    def filter_tagged(self, queryset):
        """Apply requested filter to the queryset."""
        # Tagged.
        if self.parameters['tagged'] == 'yes':
            queryset = queryset.filter(tags__isnull=False)

        if self.parameters['tagged'] == 'auto':
            queryset = queryset.filter(tagtothread__automatically_added=True)

        if self.parameters['tagged'] == 'user':
            queryset = queryset.filter(tagtothread__automatically_added=False)

        if self.parameters['tagged'] == 'no':
            queryset = queryset.filter(tags__isnull=True)

        return queryset

    def filter_last_reply(self, queryset):
        """Apply requested filter to the queryset."""
        # Last reply.
        if not self.parameters['last_reply'] == 'always':
            time_threshold = datetime.datetime.now().replace(tzinfo=utc) - datetime.timedelta(
                hours=self.last_reply_times[self.parameters['last_reply']]
            )
            queryset = queryset.filter(last_reply__gt=time_threshold)

        return queryset

    def filter_tag(self, queryset):
        """Apply requested filter to the queryset."""
        if not self.parameters['tag'] is None:
            for tag in self.parameters['tag']:
                queryset = queryset.filter(tags__name=tag)

        return queryset

    def sort(self, queryset):
        """Apply requested sorting to the queryset."""
        if self.parameters['sort'] == 'last_reply':
            queryset = queryset.order_by('-last_reply' if self.parameters['sort_reverse'] else 'last_reply')

        if self.parameters['sort'] == 'creation_date':
            queryset = queryset.annotate(first_reply=Min('post__time')).order_by(
                '-first_reply' if self.parameters['sort_reverse'] else 'first_reply'
            )

        if self.parameters['sort'] == 'replies':
            queryset = queryset.annotate(
                replies=Count('post')).order_by('-replies' if self.parameters['sort_reverse'] else 'replies'
            )

        return queryset

    def get_queryset(self):
        name = self.kwargs['name']
        self.parameters = self.get_parameters()

        # I don't know how to select all data I need without executing
        # TWO damn additional queries for each thread (first post + tags).
        queryset = Thread.objects.filter(board=name).annotate(
            replies_count=Count('post'),
            images_count=Count('post__image'),
            last_reply=Max('post__time'),
        ).filter(replies_count__gte=1)

        queryset = self.filter_saved(queryset)
        queryset = self.filter_tagged(queryset)
        queryset = self.filter_last_reply(queryset)
        queryset = self.filter_tag(queryset)

        queryset = self.sort(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(BoardView, self).get_context_data(**kwargs)
        context['board_name'] = self.kwargs['name']
        context['parameters'] = self.parameters
        context['available_parameters'] = self.available_parameters
        context['body_id'] = 'body-board'
        return context


class ThreadView(ListView):
    """View showing all posts in a specified thread."""
    model = Thread
    context_object_name = 'post_list'
    template_name = 'archive_chan/thread.html'

    def get_queryset(self):
        name = self.kwargs['name']
        number = self.kwargs['number']
        self.thread = get_object_or_404(Thread, board=name, number=number)
        return get_list_or_404(Post.objects.filter(
            thread__number=number,
            thread__board=name
        ).order_by('number').select_related('image'))

    def get_context_data(self, **kwargs):
        context = super(ThreadView, self).get_context_data(**kwargs)
        context['board_name'] = self.kwargs['name']
        context['thread_number'] = int(self.kwargs['number'])
        context['thread_saved'] = self.thread.saved
        context['thread_tags'] = self.thread.tagtothread_set.select_related('tag').all().order_by('tag__name')
        context['body_id'] = 'body-thread'
        return context


def ajax_save_thread(request):
    """View used for AJAX save thread calls."""
    response = {}

    if request.user.is_authenticated():
        try:
            thread_number = int(request.GET['thread'])
            board_name = request.GET['board']
            state = request.GET['state']

            state = (state == 'true')

            thread = Thread.objects.get(board=board_name, number=thread_number)
            thread.saved = state
            thread.save()

            response = {
                'state': thread.saved
            }

        except:
            response = {
                'error': 'Error.'
            }
    else:
        response = {
            'error': 'Log in.'
        }

    return HttpResponse(json.dumps(response), content_type='application/json')


def ajax_get_parent_thread(request):
    """Returns a number of a thread the specified post belongs to."""
    response = {}

    try:
        post_number = int(request.GET['post'])
        board_name = request.GET['board']

        parent_thread_number = Post.objects.get(thread__board=board_name, number=post_number).thread.number

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

    if request.user.is_authenticated():
        try:
            thread_number = int(request.GET['thread'])
            board_name = request.GET['board']
            tag = request.GET['tag']

            exists = TagToThread.objects.filter(
                thread__number=thread_number, 
                thread__board__name=board_name,
                tag__name=tag
            ).exists()

            if not exists:
                thread = Thread.objects.get(number=thread_number, board__name=board_name)

                try:
                    tag = Tag.objects.get(name=tag)

                except: # Create new.
                    tag = Tag(name=tag)
                    tag.save()

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
            'error': 'Log in.'
        }

    return HttpResponse(json.dumps(response), content_type='application/json')


def ajax_remove_tag(request):
    """View used to remove a tag related to a thread."""
    response = {}

    if request.user.is_authenticated():
        try:
            thread_number = int(request.GET['thread'])
            board_name = request.GET['board']
            tag = request.GET['tag']

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
            'error': 'Log in.'
        }

    return HttpResponse(json.dumps(response), content_type='application/json')
