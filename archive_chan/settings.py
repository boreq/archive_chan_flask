"""
    Default settings for the application.

    Of course you can modify those values directly in this file but that might
    cause problems while updating the repository. You will also be unable to
    return to the default values simply by deleting the line in the custom file.
"""

API_WAIT = 1 # [seconds] Delay between two API calls (catalog/list of posts). This should follow the API rules.
FILE_WAIT = 0 # [seconds] Delay between two file downloads (images/thumbnails). This should follow the API rules (no limit at this point).
CONNECTION_TIMEOUT = 10 # [seconds] Code downloading the data will stop waiting for a response after that time.
RECENT_POSTS_AGE = 48 # [hours] Used for selecting statistics when the board stores posts forever without deleting them. Read more in views.ajax_board_stats
SCRAPER_THREADS_NUMBER = 1 # Number of additional program threads running at the same time. In other words that many 4chan threads will be updated at the same time.
VIEW_CACHE_AGE = 60 * 5 # [seconds] max age of the dynamic pages eg. board
VIEW_CACHE_AGE_STATIC = 60 * 60 * 24 # [seconds] max age of the static pages eg. stats

SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:password@localhost/archive_chan_0649c24'
MEDIA_ROOT = '/home/filip/www/media'
