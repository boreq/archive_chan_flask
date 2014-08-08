from flask import Flask
from werkzeug.contrib.cache import MemcachedCache, BaseCache
from flask_debugtoolbar import DebugToolbarExtension

# Init the application object.
app = Flask(__name__)

# Load config.
app.config.from_object('archive_chan.settings')
app.config.from_envvar('BROWN_SETTINGS', True)

app.config['DEBUG'] = True

# Init cache.
if not app.config['DEBUG']:
    cache = MemcachedCache(app.config['MEMCACHED_URL']) # Actual memcached.
else:
    cache = BaseCache() # Base cache class which does literally nothing.
    try:
        from flask_debugtoolbar import DebugToolbarExtension
        if not app.config.get('SECRET_KEY'):
            # I don't know a better way to get random data.
            app.config['SECRET_KEY'] = 'LOLOLOLOLOLOLOLOLOL'
        toolbar = DebugToolbarExtension(app)
    except ImportError as e:
        import sys
        sys.stderr.write('Flask Debug Toolbar was NOT loaded. Error: %s\n' % e)


from .archive_chan.database import db
db.init_app(app)
from .archive_chan import bl
app.register_blueprint(bl)
