


class SearchView(UniversalViewMixin, ListView):
    """View showing all threads in a specified board."""
    model = Post
    context_object_name = 'post_list'
    template_name = 'archive_chan/search.html'
    paginate_by = 20
    body_id = 'body-search'

    available_parameters = {
        'type': (
            ('all', ('All', None)),
            ('op', ('Main post', {'number': F('thread__number')})),
        ),
        'saved': (
            ('all', ('All', None)),
            ('yes', ('Yes', {'thread__saved': True})),
            ('no',  ('No', {'thread__saved': False})),
        ),
        'created': (
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

        self.modifiers['type'] = modifiers.SimpleFilter(
            self.available_parameters['type'],
            self.request.GET.get('type', None)
        )

        self.modifiers['created'] = modifiers.TimeFilter(
            self.available_parameters['created'],
            self.request.GET.get('created', None)
        )

        parameters['saved'] = self.modifiers['saved'].get()
        parameters['created'] = self.modifiers['created'].get()
        parameters['type'] = self.modifiers['type'].get()
        parameters['search'] = self.request.GET.get('search', None)

        return parameters

    def get_queryset(self):
        self.parameters = self.get_parameters()
        self.chart_data = None

        if self.parameters['search'] is None or len(self.parameters['search']) == 0:
            return Post.objects.none()

        queryset = Post.objects

        if 'board' in self.kwargs:
            queryset = queryset.filter(thread__board=self.kwargs['board'])

        if 'thread' in self.kwargs:
            queryset = queryset.filter(thread__number=self.kwargs['thread'])
        
        queryset = queryset.filter(
            Q(subject__icontains=self.parameters['search']) |
            Q(comment__icontains=self.parameters['search'])
        ).order_by('-time')
        
        for key, modifier in self.modifiers.items():
            queryset = modifier.execute(queryset)

        self.chart_data = queryset.extra({
            'date': 'date("time")',
        }).values('date').order_by('date').annotate(amount=Count('id'))

        return queryset.select_related('thread', 'image', 'thread__board')

    def get_context_data(self, **kwargs):
        from archive_chan.lib.stats import get_posts_chart_data

        context = super(SearchView, self).get_context_data(**kwargs)
        context['parameters'] = self.parameters
        context['available_parameters'] = self.available_parameters
        context['chart_data'] = get_posts_chart_data(self.chart_data)
        return context
