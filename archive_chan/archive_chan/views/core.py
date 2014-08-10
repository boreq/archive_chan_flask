import operator
from flask import render_template, request
from flask.views import View
from ..models import Board, Thread, Post, Image, TagToThread
from ..lib import modifiers, pagination
from ..lib.helpers import get_object_or_404

class TemplateView(View):
    def get_context_data(self, **kwargs):
        return {}

    def dispatch_request(self, *args, **kwargs):
        self.kwargs = kwargs
        context = self.get_context_data()
        return render_template(self.template_name, **context)


class BodyIdMixin(object):
    """This mixin adds an easy way to add body_id to the context."""
    def get_context_data(self, **kwargs):
        context = super(BodyIdMixin, self).get_context_data(**kwargs)
        context['body_id'] = getattr(self, 'body_id', None)
        return context


class UniversalViewMixin(BodyIdMixin):
    """This mixin automatically adds board_name and thread_number to the context."""
    def get_context_data(self, **kwargs):
        context = super(UniversalViewMixin, self).get_context_data(**kwargs)
        context['board_name'] = self.kwargs.get('board', None)
        context['thread_number'] = int(self.kwargs['thread']) if 'thread' in self.kwargs else None
        return context


class IndexView(BodyIdMixin, TemplateView):
    """View showing all boards."""
    template_name = 'archive_chan/index.html'
    body_id = 'body-home'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['board_list'] = Board.query.order_by('name').all()
        return context


class BoardView(BodyIdMixin, TemplateView):
    """View showing all threads in a specified board."""
    template_name = 'archive_chan/board.html'
    body_id = 'body-board'
    available_parameters = {
        'sort': (
            ('last_reply', ('Last reply', Thread.last_reply, None)),
            ('creation_date', ('Creation date', Thread.first_reply, None)),
            ('replies', ('Replies', Thread.replies, None)),
            ('images', ('Images', Thread.images, None)),
        ),
        'saved': (
            ('all', ('All', None)),
            ('yes', ('Yes', (Thread.saved==True,))),
            ('no',  ('No', (Thread.saved==False,))),
        ),
        'last_reply': (
            ('always', ('Always', None)),
            ('quarter', ('15 minutes', (operator.gt, Thread.last_reply, 0.25))),
            ('hour', ('Hour', (operator.gt, Thread.last_reply, 1))),
            ('day', ('Day', (operator.gt, Thread.last_reply, 24))),
            ('week', ('Week', (operator.gt, Thread.last_reply, 24 * 7))),
            ('month', ('Month', (operator.gt, Thread.last_reply, 24 * 30))),
        ),
        'tagged': (
            ('all', ('All', None)),
            ('yes', ('Yes', (Thread.tags.any(),))),
            ('auto', ('Automatically', (Thread.tagtothreads.any(TagToThread.automatically_added==True),))),
            ('user', ('Manually', (Thread.tagtothreads.any(TagToThread.automatically_added==False),))),
            ('no', ('No', (~Thread.tags.any(),))),
        )
    }

    def get_parameters(self):
        """Extracts parameters related to filtering and sorting from a request object."""
        parameters = {}

        self.modifiers = {}

        self.modifiers['sort'] = modifiers.SimpleSort(
            self.available_parameters['sort'],
            request.args.get('sort', None)
        )

        self.modifiers['saved'] = modifiers.SimpleFilter(
            self.available_parameters['saved'],
            request.args.get('saved', None)
        )

        self.modifiers['tagged'] = modifiers.SimpleFilter(
            self.available_parameters['tagged'],
            request.args.get('tagged', None)
        )

        self.modifiers['last_reply'] = modifiers.TimeFilter(
            self.available_parameters['last_reply'],
            request.args.get('last_reply', None)
        )

        self.modifiers['tag'] = modifiers.TagFilter(
            request.args.get('tag', None)
        )

        parameters['sort'], parameters['sort_reverse'] = self.modifiers['sort'].get()
        parameters['sort_with_operator'] = self.modifiers['sort'].get_full()
        parameters['saved'] = self.modifiers['saved'].get()
        parameters['tagged'] = self.modifiers['tagged'].get()
        parameters['last_reply'] = self.modifiers['last_reply'].get()
        parameters['tag'] = self.modifiers['tag'].get()

        return parameters

    def get_queryset(self):
        # I don't know how to select all data I need using the ORM without executing
        # TWO damn additional queries for each thread (first post + tags).
        #queryset = Thread.objects.filter(board=self.kwargs['board'], replies__gte=1).select_related('board')

        queryset = Thread.query.join(Board).filter(
            Board.name==self.kwargs['board'],
            Thread.replies>1
        )

        for key, modifier in self.modifiers.items():
            queryset = modifier.execute(queryset)
        #queryset = self.modifiers['saved'].execute(queryset)
        #queryset = queryset.filter(Thread.saved==True)

        return queryset.limit(20)

    def get_context_data(self, **kwargs):
        context = super(BoardView, self).get_context_data(**kwargs)
        self.parameters = self.get_parameters()
        context['board_name'] = self.kwargs['board']
        context['thread_list'] = self.get_queryset()
        context['parameters'] = self.parameters
        context['available_parameters'] = self.available_parameters
        return context


class ThreadView(UniversalViewMixin, TemplateView):
    """View showing all posts in a specified thread."""
    template_name = 'archive_chan/thread.html'
    body_id = 'body-thread'

    def get_queryset(self):
        return Post.query.join(Thread, Board).filter(
            Thread.number==self.kwargs['thread'],
            Board.name==self.kwargs['board']
        ).order_by(Post.number)

    def get_context_data(self, **kwargs):
        context = super(ThreadView, self).get_context_data(**kwargs)
        context['post_list'] = self.get_queryset()
        return context


class GalleryView(UniversalViewMixin, TemplateView):
    """View displaying gallery template. Data is loaded via AJAX calls."""
    template_name = 'archive_chan/gallery.html'
    body_id = 'body-gallery'


class StatsView(UniversalViewMixin, TemplateView):
    """View displaying stats template. Data is loaded via AJAX calls."""
    template_name = 'archive_chan/stats.html'
    body_id = 'body-stats'


class StatusView(BodyIdMixin, TemplateView):
    """View displaying archive status. Data is loaded via AJAX calls."""
    template_name = 'archive_chan/status.html'
    body_id = 'body-status'
