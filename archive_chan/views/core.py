import operator
from flask import Blueprint, render_template, request
from flask.views import View
from ..models import Board, Thread, Post, Image, TagToThread
from ..lib import modifiers
from ..lib.pagination import Pagination
from ..lib.helpers import get_object_or_404


bl = Blueprint('core', __name__)


class TemplateView(View):
    def get_context_data(self, **kwargs):
        return {}

    def dispatch_request(self, *args, **kwargs):
        self.kwargs = kwargs
        context = self.get_context_data()
        return render_template(self.template_name, **context)


class BodyIdMixin(object):
    """Adds an easy way to add body_id to the context."""
    def get_context_data(self, **kwargs):
        context = super(BodyIdMixin, self).get_context_data(**kwargs)
        context['body_id'] = getattr(self, 'body_id', None)
        return context


class UniversalViewMixin(BodyIdMixin):
    """Adds board_name and thread_number to the context."""
    def get_context_data(self, **kwargs):
        context = super(UniversalViewMixin, self).get_context_data(**kwargs)
        context['board_name'] = self.kwargs.get('board', None)
        context['thread_number'] = int(self.kwargs['thread'])
                                   if 'thread' in self.kwargs else None
        return context


class IndexView(BodyIdMixin, TemplateView):
    """View showing all boards."""
    template_name = 'core/index.html'
    body_id = 'body-home'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['board_list'] = Board.query.order_by('name').all()
        return context


class BoardView(BodyIdMixin, TemplateView):
    """View showing all threads in a specified board."""
    template_name = 'core/board.html'
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
            ('auto', ('Automatically', (Thread.tagtothreads.any(
                TagToThread.automatically_added==True
            ),))),
            ('user', ('Manually', (Thread.tagtothreads.any(
                TagToThread.automatically_added==False
            ),))),
            ('no', ('No', (~Thread.tags.any(),))),
        )
    }

    def get_parameters(self):
        """Extracts parameters related to filtering and sorting from
        the request object.
        """
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

        parameters = {}
        parameters['sort'], parameters['sort_reverse'] = self.modifiers['sort'].get()
        parameters['sort_with_operator'] = self.modifiers['sort'].get_full()
        parameters['saved'] = self.modifiers['saved'].get()
        parameters['tagged'] = self.modifiers['tagged'].get()
        parameters['last_reply'] = self.modifiers['last_reply'].get()
        parameters['tag'] = self.modifiers['tag'].get()
        return parameters

    def get_queryset(self):
        queryset = Thread.query.join(Board).filter(
            Board.name==self.kwargs['board'],
            Thread.replies>1
        )

        for key, modifier in self.modifiers.items():
            queryset = modifier.execute(queryset)

        total_count = queryset.count()

        self.pagination = Pagination(
            request.args.get('page'),
            20,
            total_count
        )
        self.parameters['page'] = self.pagination.page

        return queryset.slice(*self.pagination.get_slice())

    def get_context_data(self, **kwargs):
        self.parameters = self.get_parameters()

        context = super(BoardView, self).get_context_data(**kwargs)
        context['board_name'] = self.kwargs['board']
        context['thread_list'] = self.get_queryset()
        context['pagination'] = self.pagination
        context['parameters'] = self.parameters
        context['available_parameters'] = self.available_parameters
        return context


class ThreadView(UniversalViewMixin, TemplateView):
    """View showing all posts in a specified thread."""
    template_name = 'core/thread.html'
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
    template_name = 'core/gallery.html'
    body_id = 'body-gallery'


class StatsView(UniversalViewMixin, TemplateView):
    """View displaying stats template. Data is loaded via AJAX calls."""
    template_name = 'core/stats.html'
    body_id = 'body-stats'


class StatusView(BodyIdMixin, TemplateView):
    """View displaying archive status. Data is loaded via AJAX calls."""
    template_name = 'core/status.html'
    body_id = 'body-status'


bl.add_url_rule('/', view_func=IndexView.as_view('index'))
bl.add_url_rule('/gallery/', view_func=GalleryView.as_view('gallery'))
bl.add_url_rule('/stats/', view_func=StatsView.as_view('stats'))
bl.add_url_rule('/status/', view_func=StatusView.as_view('status'))

bl.add_url_rule('/board/<board>/', view_func=BoardView.as_view('board'))
bl.add_url_rule('/board/<board>/gallery/', view_func=GalleryView.as_view('board_gallery'))
bl.add_url_rule('/board/<board>/stats/', view_func=StatsView.as_view('board_stats'))

bl.add_url_rule('/board/<board>/thread/<thread>/', view_func=ThreadView.as_view('thread'))
bl.add_url_rule('/board/<board>/thread/<thread>/gallery/', view_func=GalleryView.as_view('thread_gallery'))
bl.add_url_rule('/board/<board>/thread/<thread>/stats/', view_func=StatsView.as_view('thread_stats'))