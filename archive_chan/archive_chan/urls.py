from flask import send_from_directory, current_app
from . import bl
from .views import core, api
#import .views.api as api

'''
urlpatterns = patterns('',
    # Global.
    url(r'^$', cache_page(cache)(core.IndexView.as_view()), name='index'),
    url(r'^stats/$', cache_page(cache_static)(core.StatsView.as_view()), name='stats'),
    url(r'^gallery/$', cache_page(cache_static)(core.GalleryView.as_view()), name='gallery'),
    url(r'^search/$', core.SearchView.as_view(), name='search'),

    # Board.
    url(r'^board/(?P<board>[a-z]+)/$', cache_page(cache)(core.BoardView.as_view()), name='board'),
    url(r'^board/(?P<board>[a-z]+)/stats/$', cache_page(cache_static)(core.StatsView.as_view()), name='board_stats'),
    url(r'^board/(?P<board>[a-z]+)/gallery/$', cache_page(cache_static)(core.GalleryView.as_view()), name='board_gallery'),
    url(r'^board/(?P<board>[a-z]+)/search/$', core.SearchView.as_view(), name='board_search'),

    # Stats.
    url(r'^board/(?P<board>[a-z]+)/thread/(?P<thread>[0-9]+)/$', ensure_csrf_cookie(core.ThreadView.as_view()), name='thread'),
    url(r'^board/(?P<board>[a-z]+)/thread/(?P<thread>[0-9]+)/stats/$', cache_page(cache_static)(core.StatsView.as_view()), name='thread_stats'),
    url(r'^board/(?P<board>[a-z]+)/thread/(?P<thread>[0-9]+)/gallery/$', cache_page(cache_static)(core.GalleryView.as_view()), name='thread_gallery'),
    url(r'^board/(?P<board>[a-z]+)/thread/(?P<thread>[0-9]+)/search/$', core.SearchView.as_view(), name='thread_search'),

    # Misc.
    url(r'^status/$', cache_page(cache_static)(core.StatusView.as_view()), name='status'),

    # API.
    url(r'^api/status/$', api.StatusView.as_view(), name='api_status'),
    url(r'^api/stats/$', api.StatsView.as_view(), name='api_stats'),
    url(r'^api/gallery/$', api.GalleryView.as_view(), name='api_gallery'),

    url(r'^ajax/thread/save/$', api.ajax_save_thread, name='ajax_save_thread'),
    url(r'^ajax/get_parent_thread/$', api.ajax_get_parent_thread, name='ajax_get_parent_thread'),

    url(r'^ajax/tag/suggest/$', api.ajax_suggest_tag, name='ajax_suggest_tag'),
    url(r'^ajax/tag/add/$', api.ajax_add_tag, name='ajax_add_tag'),
    url(r'^ajax/tag/remove/$', api.ajax_remove_tag, name='ajax_remove_tag'),
)
'''

bl.add_url_rule('/', view_func=core.IndexView.as_view('index'))
bl.add_url_rule('/gallery/', view_func=core.GalleryView.as_view('gallery'))
bl.add_url_rule('/stats/', view_func=core.StatsView.as_view('stats'))

bl.add_url_rule('/board/<board>/', view_func=core.BoardView.as_view('board'))
bl.add_url_rule('/board/<board>/gallery/', view_func=core.GalleryView.as_view('board_gallery'))
bl.add_url_rule('/board/<board>/stats/', view_func=core.StatsView.as_view('board_stats'))

bl.add_url_rule('/board/<board>/thread/<thread>/', view_func=core.ThreadView.as_view('thread'))
bl.add_url_rule('/board/<board>/thread/<thread>/gallery/', view_func=core.GalleryView.as_view('thread_gallery'))
bl.add_url_rule('/board/<board>/thread/<thread>/stats/', view_func=core.StatsView.as_view('thread_stats'))

bl.add_url_rule('/api/gallery/', view_func=api.GalleryView.as_view('api_gallery'))
bl.add_url_rule('/api/stats/', view_func=api.StatsView.as_view('api_stats'))

@bl.route('/media/<path:filename>')
def media(filename):
    return send_from_directory(current_app.config['MEDIA_ROOT'], filename)
