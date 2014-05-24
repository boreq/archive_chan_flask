from django.conf.urls import patterns, url
from archive_chan import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^board/(?P<name>[a-z]+)/$', views.BoardView.as_view(), name='board'),
    url(r'^board/(?P<name>[a-z]+)/thread/(?P<number>[0-9]+)/$', views.ThreadView.as_view(), name='thread'),

    url(r'^ajax/save/$', views.ajax_save_thread, name='ajax_save_thread'),
    url(r'^ajax/get_parent_thread/$', views.ajax_get_parent_thread, name='ajax_get_parent_thread'),

    url(r'^ajax/tag/suggest$', views.ajax_suggest_tag, name='ajax_suggest_tag'),
    url(r'^ajax/tag/add$', views.ajax_add_tag, name='ajax_add_tag'),
    url(r'^ajax/tag/remove$', views.ajax_remove_tag, name='ajax_remove_tag'),
)
