from django.conf.urls import patterns, url
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_page

from archive_chan import views
from archive_chan.settings import AppSettings

cache = AppSettings.get('VIEW_CACHE_AGE')
cache_static = AppSettings.get('VIEW_CACHE_AGE_STATIC')

urlpatterns = patterns('',
    # Global.
    url(r'^$', cache_page(cache)(views.IndexView.as_view()), name='index'),
    url(r'^stats/$', cache_page(cache_static)(views.StatsView.as_view()), name='stats'),
    url(r'^gallery/$', cache_page(cache_static)(views.GalleryView.as_view()), name='gallery'),
    url(r'^search/$', views.SearchView.as_view(), name='search'),

    # Board.
    url(r'^board/(?P<board>[a-z]+)/$', cache_page(cache)(views.BoardView.as_view()), name='board'),
    url(r'^board/(?P<board>[a-z]+)/stats/$', cache_page(cache_static)(views.StatsView.as_view()), name='board_stats'),
    url(r'^board/(?P<board>[a-z]+)/gallery/$', cache_page(cache_static)(views.GalleryView.as_view()), name='board_gallery'),
    url(r'^board/(?P<board>[a-z]+)/search/$', views.SearchView.as_view(), name='board_search'),

    # Stats.
    url(r'^board/(?P<board>[a-z]+)/thread/(?P<thread>[0-9]+)/$', ensure_csrf_cookie(views.ThreadView.as_view()), name='thread'),
    url(r'^board/(?P<board>[a-z]+)/thread/(?P<thread>[0-9]+)/stats/$', cache_page(cache_static)(views.StatsView.as_view()), name='thread_stats'),
    url(r'^board/(?P<board>[a-z]+)/thread/(?P<thread>[0-9]+)/gallery/$', cache_page(cache_static)(views.GalleryView.as_view()), name='thread_gallery'),
    url(r'^board/(?P<board>[a-z]+)/thread/(?P<thread>[0-9]+)/search/$', views.SearchView.as_view(), name='thread_search'),

    # AJAX.
    url(r'^ajax/stats/$', views.ajax_stats, name='ajax_stats'),
    url(r'^ajax/gallery/$', views.ajax_gallery, name='ajax_gallery'),

    url(r'^ajax/thread/save/$', views.ajax_save_thread, name='ajax_save_thread'),
    url(r'^ajax/get_parent_thread/$', views.ajax_get_parent_thread, name='ajax_get_parent_thread'),

    url(r'^ajax/tag/suggest/$', views.ajax_suggest_tag, name='ajax_suggest_tag'),
    url(r'^ajax/tag/add/$', views.ajax_add_tag, name='ajax_add_tag'),
    url(r'^ajax/tag/remove/$', views.ajax_remove_tag, name='ajax_remove_tag'),
)
