"""
    Default settings.

    Path to the custom settings file should be specified in the
    ARCHIVE_CHAN_SETTINGS environment variable. Settings defined there will
    overwrite values present in this file. If you want to run multiple
    instances of the archive with different configs you can change the name
    of the environment variable by passing the parameter to the application
    factory. See the source code in __init__.py for more details.

    Of course you can modify this file directly but that might cause conflicts
    while updating the repository and it is a good practice to keep the default
    values for reference. Furthermore it would be impossible to run multiple
    instances that way and your modification could influence unit testing.
"""


# Delay between two calls to 4chan API (catalog/posts).
# This should follow the API rules: https://github.com/4chan/4chan-API
# [seconds]
API_WAIT = 1

# Delay between two file downloads (images/thumbnails).
# This should follow the API rules (no limit at this point).
# [seconds]
FILE_WAIT = 0

# Code downloading the data will stop waiting for a response after that time.
# [seconds]
CONNECTION_TIMEOUT = 10

# Used for calculating statistics (e.g. posts per hour).
# Read more in lib.stats
# [hours]
RECENT_POSTS_AGE = 48 

# Number of additional scraper threads running at the same time.
# In other words that many 4chan threads will be updated concurrently.
SCRAPER_THREADS_NUMBER = 4

# Max cache age.
# Cache is disabled in DEBUG or TESTING mode.
# See cache.get_preferred_cache_system to learn more.
# [seconds]
CACHE_TIMEOUT = 60 * 5

# Memcached url. Set to None to disable. Must be a tuple or a list.
MEMCACHED_URL = ['127.0.0.1:11211']

# Database URI.
# https://pythonhosted.org/Flask-SQLAlchemy/config.html#configuration-keys
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/archive_chan'

# Directory to which the images will be downloaded.
MEDIA_ROOT = '/path/to/media/directory/'

# Secret key is used by Flask to handle sessions. Set it to random value. 
SECRET_KEY = 'dev_key'
