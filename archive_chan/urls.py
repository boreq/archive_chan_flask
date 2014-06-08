from django.conf.urls import patterns, url
from django.views.decorators.csrf import ensure_csrf_cookie

from archive_chan import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^board/(?P<name>[a-z]+)/$', views.BoardView.as_view(), name='board'),
    url(r'^board/(?P<name>[a-z]+)/stats/$', views.StatsView.as_view(), name='board_stats'),
    url(r'^board/(?P<name>[a-z]+)/gallery/$', views.GalleryView.as_view(), name='board_gallery'),
    url(r'^board/(?P<name>[a-z]+)/search/$', views.SearchView.as_view(), name='board_search'),

    url(r'^board/(?P<name>[a-z]+)/thread/(?P<number>[0-9]+)/$', ensure_csrf_cookie(views.ThreadView.as_view()), name='thread'),
    url(r'^board/(?P<name>[a-z]+)/thread/(?P<number>[0-9]+)/stats/$', views.StatsView.as_view(), name='thread_stats'),
    url(r'^board/(?P<name>[a-z]+)/thread/(?P<number>[0-9]+)/gallery/$', views.GalleryView.as_view(), name='thread_gallery'),
    url(r'^board/(?P<name>[a-z]+)/thread/(?P<number>[0-9]+)/search/$', views.SearchView.as_view(), name='thread_search'),

    url(r'^stats/$', views.StatsView.as_view(), name='stats'),
    url(r'^gallery/$', views.GalleryView.as_view(), name='gallery'),
    url(r'^search/$', views.SearchView.as_view(), name='search'),

    url(r'^ajax/stats/$', views.ajax_stats, name='ajax_stats'),
    url(r'^ajax/gallery/$', views.ajax_gallery, name='ajax_gallery'),

    url(r'^ajax/thread/save/$', views.ajax_save_thread, name='ajax_save_thread'),
    url(r'^ajax/get_parent_thread/$', views.ajax_get_parent_thread, name='ajax_get_parent_thread'),

    url(r'^ajax/tag/suggest/$', views.ajax_suggest_tag, name='ajax_suggest_tag'),
    url(r'^ajax/tag/add/$', views.ajax_add_tag, name='ajax_add_tag'),
    url(r'^ajax/tag/remove/$', views.ajax_remove_tag, name='ajax_remove_tag'),
)
