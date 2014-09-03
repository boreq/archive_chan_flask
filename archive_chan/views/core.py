import operator
from collections import defaultdict
from flask import Blueprint, render_template, request
from flask.views import View
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from ..cache import CachedBlueprint
from ..models import Board, Thread, Post, Image, TagToThread
from ..lib import modifiers
from ..lib.pagination import Pagination


bl = CachedBlueprint('core', __name__, vary_on_auth=True)


class TemplateView(View):
    """Base view which renders a template with context returned by
    get_context_data method.
    """

    def get_context_data(self, *args, **kwargs):
        return {}

    def dispatch_request(self, *args, **kwargs):
        self.kwargs = kwargs
        context = self.get_context_data(*args, **kwargs)
        return render_template(self.template_name, **context)


class BodyIdMixin(object):
    """Adds an easy way to add body_id to the context."""

    def get_context_data(self, *args, **kwargs):
        context = super(BodyIdMixin, self).get_context_data(*args, **kwargs)
        context['body_id'] = getattr(self, 'body_id', None)
        return context


class UniversalViewMixin(BodyIdMixin):
    """Adds board_name and thread_number to the context."""

    def get_context_data(self, *args, **kwargs):
        context = super(UniversalViewMixin, self).get_context_data(*args, **kwargs)
        context['board_name'] = self.kwargs.get('board', None)
        context['thread_number'] = int(self.kwargs['thread']) \
            if 'thread' in self.kwargs else None
        return context


class IndexView(BodyIdMixin, TemplateView):
    """View showing all boards."""

    template_name = 'core/index.html'
    body_id = 'body-home'

    def get_context_data(self, *args, **kwargs):
        context = super(IndexView, self).get_context_data(*args, **kwargs)
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
        queryset = Thread.query.join(Board) \
                               .options(joinedload('first_post')) \
                               .filter(Board.name==self.kwargs['board'],
                                       Thread.replies>1)

        for key, modifier in self.modifiers.items():
            queryset = modifier.execute(queryset)

        total_count = queryset.count()

        self.pagination = Pagination(request.args.get('page'), 20, total_count)
        self.parameters['page'] = self.pagination.page

        return queryset.slice(*self.pagination.get_slice()).all()

    def get_tags(self, queryset):
        """Gets all TagToThreads in one query and creates a dictionary
        thread.id -> [Tag, ...]
        Threads without tags are missing.
        """
        if not queryset:
            return {}
        thread_ids = [thread.id for thread in queryset]
        tagtothreads = TagToThread.query.filter(TagToThread.thread_id.in_(thread_ids)) \
                                  .options(joinedload('thread')) \
                                  .all()
        tag_dict = defaultdict(lambda: [])
        for tagtothread in tagtothreads:
            tag_dict[tagtothread.thread_id].append(tagtothread.tag)
        return tag_dict

    def get_context_data(self, *args, **kwargs):
        self.parameters = self.get_parameters()

        context = super(BoardView, self).get_context_data(*args, **kwargs)
        context['board_name'] = self.kwargs['board']
        context['thread_list'] = self.get_queryset()
        context['tags'] = self.get_tags(context['thread_list'])
        context['pagination'] = self.pagination
        context['parameters'] = self.parameters
        context['available_parameters'] = self.available_parameters
        return context


class ThreadView(UniversalViewMixin, TemplateView):
    """View showing all posts in a specified thread."""

    template_name = 'core/thread.html'
    body_id = 'body-thread'

    def get_queryset(self):
        return Post.query.join(Thread, Board) \
                         .filter(Thread.number==self.kwargs['thread'],
                                 Board.name==self.kwargs['board']) \
                         .order_by(Post.number) \
                         .all()

    def get_context_data(self, *args, **kwargs):
        context = super(ThreadView, self).get_context_data(*args, **kwargs)
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


class SearchView(UniversalViewMixin, TemplateView):
    """Allows the user to perform searches."""

    template_name = 'core/search.html'
    body_id = 'body-search'

    available_parameters = {
        'type': (
            ('all', ('All', None)),
            ('op', ('Main post', (Post.number==Thread.number,))),
            ('reply', ('Reply', (Post.number!=Thread.number,))),
        ),
        'saved': (
            ('all', ('All', None)),
            ('yes', ('Yes', (Thread.saved==True,))),
            ('no',  ('No', (Thread.saved==False,))),
        ),
        'created': (
            ('always', ('Always', None)),
            ('quarter', ('15 minutes', (operator.gt, Thread.last_reply, 0.25))),
            ('hour', ('Hour', (operator.gt, Thread.last_reply, 1))),
            ('day', ('Day', (operator.gt, Thread.last_reply, 24))),
            ('week', ('Week', (operator.gt, Thread.last_reply, 24 * 7))),
            ('month', ('Month', (operator.gt, Thread.last_reply, 24 * 30))),
        ),
    }

    def get_parameters(self):
        """Extracts parameters related to filtering and sorting from request."""
        self.modifiers = {}
        self.modifiers['saved'] = modifiers.SimpleFilter(
            self.available_parameters['saved'],
            request.args.get('saved', None)
        )
        self.modifiers['type'] = modifiers.SimpleFilter(
            self.available_parameters['type'],
            request.args.get('type', None)
        )
        self.modifiers['created'] = modifiers.TimeFilter(
            self.available_parameters['created'],
            request.args.get('created', None)
        )

        parameters = {}
        parameters['saved'] = self.modifiers['saved'].get()
        parameters['created'] = self.modifiers['created'].get()
        parameters['type'] = self.modifiers['type'].get()
        parameters['search'] = request.args.get('search', '')
        return parameters

    def get_queryset(self):
        if self.parameters['search'] is None or len(self.parameters['search']) == 0:
            self.pagination = Pagination(0, 0, 0)
            return []

        queryset = Post.query.join(Thread, Board)

        if 'board' in self.kwargs:
            queryset = queryset.filter(Board.name==self.kwargs['board'])
        if 'thread' in self.kwargs:
            queryset = queryset.filter(Thread.number==self.kwargs['thread'])
        for key, modifier in self.modifiers.items():
            queryset = modifier.execute(queryset)

        queryset = queryset.filter(
            or_(Post.subject.ilike('%' + self.parameters['search'] + '%'),
                Post.comment.ilike('%' + self.parameters['search'] + '%'))
        ).order_by(Post.time.desc())

        total_count = queryset.count()

        self.pagination = Pagination(request.args.get('page'), 20, total_count)
        self.parameters['page'] = self.pagination.page

        return queryset.slice(*self.pagination.get_slice()).all()

    def get_context_data(self, *args, **kwargs):
        self.parameters = self.get_parameters()
        context = super(SearchView, self).get_context_data(*args, **kwargs)
        context['post_list'] = self.get_queryset()
        context['pagination'] = self.pagination
        context['parameters'] = self.parameters
        context['available_parameters'] = self.available_parameters
        return context


bl.add_url_rule('/', view_func=IndexView.as_view('index'))
bl.add_url_rule('/gallery/', view_func=GalleryView.as_view('gallery'))
bl.add_url_rule('/stats/', view_func=StatsView.as_view('stats'))
bl.add_url_rule('/status/', view_func=StatusView.as_view('status'))
bl.add_url_rule('/search/', view_func=SearchView.as_view('search'))

bl.add_url_rule('/board/<board>/', view_func=BoardView.as_view('board'))
bl.add_url_rule('/board/<board>/gallery/', view_func=GalleryView.as_view('board_gallery'))
bl.add_url_rule('/board/<board>/stats/', view_func=StatsView.as_view('board_stats'))
bl.add_url_rule('/board/<board>/search/', view_func=SearchView.as_view('board_search'))

bl.add_url_rule('/board/<board>/thread/<thread>/', view_func=ThreadView.as_view('thread'))
bl.add_url_rule('/board/<board>/thread/<thread>/gallery/', view_func=GalleryView.as_view('thread_gallery'))
bl.add_url_rule('/board/<board>/thread/<thread>/stats/', view_func=StatsView.as_view('thread_stats'))
bl.add_url_rule('/board/<board>/thread/<thread>/search/', view_func=SearchView.as_view('thread_search'))
