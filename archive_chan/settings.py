# App level default settings.
# To override those in the main project settings file use
#
# ARCHIVE_CHAN_<name from the list 'app_settings' below>
#
# For example:
#
# ARCHIVE_CHAN_API_WAIT = 2

from django.conf import settings

class AppSettings:
    app_settings = {
        'API_WAIT': 1, # [seconds] Delay between two API calls (catalog/list of posts). This should follow the API rules.
        'FILE_WAIT': 0, # [seconds] Delay between two file downloads (images/thumbnails). This should follow the API rules (no limit at this point).
        'CONNECTION_TIMEOUT': 10, # [seconds] Code downloading the data will stop waiting for a response after that time.
        'RECENT_POSTS_AGE': 48, # [hours] Used for selecting statistics when the board stores posts forever without deleting them. Read more in views.ajax_board_stats
        'SCRAPER_THREADS_NUMBER': 4, # Number of additional program threads running at the same time. In other words that many 4chan threads will be updated at the same time.
    }

    @classmethod
    def get(self, name):
        return getattr(settings, 'ARCHIVE_CHAN_' + name, self.app_settings[name])
