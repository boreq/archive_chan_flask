import json, datetime, time

from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.template import RequestContext
from django.http import HttpResponse
from django.utils.timezone import utc
from django.db.models import Max, Min, Count, Q
from django.views.generic import ListView, TemplateView
from django.core.urlresolvers import reverse

from archive_chan.models import Board, Thread, Post, Tag, TagToThread, Image
import archive_chan.lib.modifiers as modifiers


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
            ('last_reply', ('Last reply', 'last_reply', None)),
            ('creation_date', ('Creation date', 'first_reply', {'first_reply': Min('post__time')})),
            ('replies', ('Replies', 'replies', {'replies': Count('post')})),
        ),
        'saved': (
            ('all', ('All', None)),
            ('yes', ('Yes', {'saved': True})),
            ('no',  ('No', {'saved': False})),
        ),
        'last_reply': (
            ('always', ('Always', None)),
            ('quarter', ('15 minutes', {'last_reply__gt': 0.25})),
            ('hour', ('Hour', {'last_reply__gt': 1})),
            ('day', ('Day', {'last_reply__gt': 24})),
            ('week', ('Week', {'last_reply__gt': 24 * 7})),
            ('month', ('Month', {'last_reply__gt': 24 * 30})),
        ),
        'tagged': (
            ('all', ('All', None)),
            ('yes', ('Yes', {'tags__isnull': False})),
            ('auto', ('Automatically', {'tagtothread__automatically_added': True})),
            ('user', ('Manually', {'tagtothread__automatically_added': False})),
            ('no', ('No', {'tags__isnull': True})),
        )
    }

    def get_parameters(self):
        """Extracts parameters related to filtering and sorting from a request object."""
        parameters = {}

        self.modifiers = {}

        self.modifiers['sort'] = modifiers.SimpleSort(
            self.available_parameters['sort'],
            self.request.GET.get('sort', None)
        )

        self.modifiers['saved'] = modifiers.SimpleFilter(
            self.available_parameters['saved'],
            self.request.GET.get('saved', None)
        )

        self.modifiers['tagged'] = modifiers.SimpleFilter(
            self.available_parameters['tagged'],
            self.request.GET.get('tagged', None)
        )

        self.modifiers['last_reply'] = modifiers.TimeFilter(
            self.available_parameters['last_reply'],
            self.request.GET.get('last_reply', None)
        )

        self.modifiers['tag'] = modifiers.TagFilter(
            self.request.GET.get('tag', None)
        )

        parameters['sort'], parameters['sort_reverse'] = self.modifiers['sort'].get()
        parameters['sort_with_operator'] = self.modifiers['sort'].get_full()
        parameters['saved'] = self.modifiers['saved'].get()
        parameters['tagged'] = self.modifiers['tagged'].get()
        parameters['last_reply'] = self.modifiers['last_reply'].get()
        parameters['tag'] = self.modifiers['tag'].get()

        return parameters

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

        for key, modifier in self.modifiers.items():
            queryset = modifier.execute(queryset)

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


class SearchView(ListView):
    """View showing all threads in a specified board."""
    model = Post
    context_object_name = 'post_list'
    template_name = 'archive_chan/search.html'
    paginate_by = 20

    available_parameters = {
        'saved': (
            ('all', ('All', None)),
            ('yes', ('Yes', {'thread__saved': True})),
            ('no',  ('No', {'thread__saved': False})),
        ),
        'age': (
            ('always', ('Always', None)),
            ('quarter', ('15 minutes', {'time': 0.25})),
            ('hour', ('Hour', {'time': 1})),
            ('day', ('Day', {'time': 24})),
            ('week', ('Week', {'time': 24 * 7})),
            ('month', ('Month', {'time': 24 * 30})),
        )
    }

    def get_parameters(self):
        """Extracts parameters related to filtering and sorting from a request object."""
        parameters = {}

        self.modifiers = {}

        self.modifiers['saved'] = modifiers.SimpleFilter(
            self.available_parameters['saved'],
            self.request.GET.get('saved', None)
        )

        self.modifiers['age'] = modifiers.TimeFilter(
            self.available_parameters['age'],
            self.request.GET.get('age', None)
        )

        parameters['saved'] = self.modifiers['saved'].get()
        parameters['age'] = self.modifiers['age'].get()
        parameters['search'] = self.request.GET.get('search', None)

        return parameters

    def get_queryset(self):
        name = self.kwargs['name']
        self.parameters = self.get_parameters()

        if self.parameters['search'] is None:
            return Post.objects.none()

        queryset = Post.objects.select_related('thread').filter(thread__board=name).filter(
            Q(subject__icontains=self.parameters['search']) |
            Q(comment__icontains=self.parameters['search'])
        )

        for key, modifier in self.modifiers.items():
            queryset = modifier.execute(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['board_name'] = self.kwargs['name']
        context['parameters'] = self.parameters
        context['available_parameters'] = self.available_parameters
        context['body_id'] = 'body-search'
        return context


class GalleryView(TemplateView):
    """View displaying gallery template. Data is loaded via AJAX calls."""
    template_name = 'archive_chan/gallery.html'

    def get_context_data(self, **kwargs):
        context = super(GalleryView, self).get_context_data(**kwargs)
        context['board_name'] = self.kwargs.get('name', None)
        context['thread_number'] = int(self.kwargs['number']) if 'number' in self.kwargs else None
        context['body_id'] = 'body-gallery'
        return context


class StatsView(TemplateView):
    """View displaying stats template. Data is loaded via AJAX calls."""
    template_name = 'archive_chan/stats.html'

    def get_context_data(self, **kwargs):
        context = super(StatsView, self).get_context_data(**kwargs)
        context['board_name'] = self.kwargs.get('name', None)
        context['thread_number'] = int(self.kwargs['number']) if 'number' in self.kwargs else None
        context['body_id'] = 'body-stats'
        return context


def ajax_stats(request):
    """JSON data with statistics."""
    from archive_chan.lib.stats import get_stats

    board_name = request.GET.get('board', None)
    thread_number = request.GET.get('thread', None)

    context = get_stats(board=board_name, thread=thread_number)

    return HttpResponse(json.dumps(context), content_type='application/json')


def ajax_gallery(request):
    """JSON data with gallery images."""

    board_name = request.GET.get('board', None)
    thread_number = request.GET.get('thread', None)
    last = request.GET.get('last', None)

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

    # If this is not a first request we have to fetch those which are not present in the gallery.
    if last is not None:
        queryset = queryset.filter(
            id__lt=last
        )

    # Grab more images if this is the first request.
    if last is not None:
        queryset = queryset.order_by('-post__time')[:10]
    else:
        queryset = queryset.order_by('-post__time')[:20]

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
            'video': image.is_webm(),
            'url': image.image.url,
            'post_url': reverse(
                'archive_chan:thread',
                args=(image.post.thread.board.name, image.post.thread.number)
            ) + format('#post-%s' % image.post.number)
        })

    return HttpResponse(json.dumps(json_data), content_type='application/json')


def ajax_save_thread(request):
    """View used for AJAX save thread calls."""
    response = {}

    if request.user.is_authenticated():
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
            'error': 'Log in.'
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

    if request.user.is_authenticated():
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
            'error': 'Log in.'
        }

    return HttpResponse(json.dumps(response), content_type='application/json')


def ajax_remove_tag(request):
    """View used to remove a tag related to a thread."""
    response = {}

    if request.user.is_authenticated():
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
            'error': 'Log in.'
        }

    return HttpResponse(json.dumps(response), content_type='application/json')
