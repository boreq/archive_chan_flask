from django.conf.urls import patterns, url
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_page

import archive_chan.views.core as core
import archive_chan.views.api as api

from archive_chan.settings import AppSettings

cache = AppSettings.get('VIEW_CACHE_AGE')
cache_static = AppSettings.get('VIEW_CACHE_AGE_STATIC')

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
    url(r'^ajax/gallery/$', core.ajax_gallery, name='ajax_gallery'),

    url(r'^ajax/thread/save/$', core.ajax_save_thread, name='ajax_save_thread'),
    url(r'^ajax/get_parent_thread/$', core.ajax_get_parent_thread, name='ajax_get_parent_thread'),

    url(r'^ajax/tag/suggest/$', core.ajax_suggest_tag, name='ajax_suggest_tag'),
    url(r'^ajax/tag/add/$', core.ajax_add_tag, name='ajax_add_tag'),
    url(r'^ajax/tag/remove/$', core.ajax_remove_tag, name='ajax_remove_tag'),
)
