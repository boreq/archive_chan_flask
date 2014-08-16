"""
    Default settings for the application.

    Path to the customized settings file should be specified in the
    ARCHIVE_CHAN_SETTINGS environment variable. Settings defined there will
    overwrite values present in this file.  

    Of course you can modify this file directly but that might cause conflicts
    while updating the repository and it is a good practice to keep the default
    values for reference.
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

# Max age of the dynamic pages (e.g. board, thread).
# [seconds]
VIEW_CACHE_AGE = 60 * 5

# Max age of the static pages (e.g. stats, gallery, status).
# [seconds]
VIEW_CACHE_AGE_STATIC = 60 * 60 * 24

# Database URI.
# https://pythonhosted.org/Flask-SQLAlchemy/config.html#configuration-keys
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/archive_chan'

# Directory to which the images will be downloaded.
MEDIA_ROOT = '/path/to/media/directory/'

# Secret key is used by Flask to handle sessions. Set it to random value. 
SECRET_KEY = 'dev_key'
