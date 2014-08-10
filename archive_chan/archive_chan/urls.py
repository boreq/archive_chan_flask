"""
    All url rules are created here.
"""


from flask import send_from_directory, current_app
from . import bl
from .views import core, api, auth


bl.add_url_rule('/', view_func=core.IndexView.as_view('index'))
bl.add_url_rule('/gallery/', view_func=core.GalleryView.as_view('gallery'))
bl.add_url_rule('/stats/', view_func=core.StatsView.as_view('stats'))
bl.add_url_rule('/status/', view_func=core.StatusView.as_view('status'))

bl.add_url_rule('/board/<board>/', view_func=core.BoardView.as_view('board'))
bl.add_url_rule('/board/<board>/gallery/', view_func=core.GalleryView.as_view('board_gallery'))
bl.add_url_rule('/board/<board>/stats/', view_func=core.StatsView.as_view('board_stats'))

bl.add_url_rule('/board/<board>/thread/<thread>/', view_func=core.ThreadView.as_view('thread'))
bl.add_url_rule('/board/<board>/thread/<thread>/gallery/', view_func=core.GalleryView.as_view('thread_gallery'))
bl.add_url_rule('/board/<board>/thread/<thread>/stats/', view_func=core.StatsView.as_view('thread_stats'))

bl.add_url_rule('/api/gallery/', view_func=api.GalleryView.as_view('api_gallery'))
bl.add_url_rule('/api/stats/', view_func=api.StatsView.as_view('api_stats'))
bl.add_url_rule('/api/status/', view_func=api.StatusView.as_view('api_status'))

bl.add_url_rule('/ajax/thread/save/', view_func=api.ajax_save_thread, methods=('POST',))
bl.add_url_rule('/ajax/get_parent_thread/', view_func=api.ajax_get_parent_thread)

bl.add_url_rule('/ajax/tag/suggest/', view_func=api.ajax_suggest_tag)
bl.add_url_rule('/ajax/tag/add/', view_func=api.ajax_add_tag, methods=('POST',))
bl.add_url_rule('/ajax/tag/remove/', view_func=api.ajax_remove_tag, methods=('POST',))

bl.add_url_rule('/login/', 'login', view_func=auth.login, methods=('GET', 'POST'))
bl.add_url_rule('/logout/', 'logout', view_func=auth.logout)


@bl.route('/media/<path:filename>')
def media(filename):
    return send_from_directory(current_app.config['MEDIA_ROOT'], filename)
