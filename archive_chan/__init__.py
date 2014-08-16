from flask import Flask
from werkzeug.contrib.cache import MemcachedCache, BaseCache


app = Flask(__name__)


# Load config.
app.config.from_object('archive_chan.settings')
app.config.from_envvar('ARCHIVE_CHAN_SETTINGS', True)


# Check if the SECRET_KEY is changed.
if not app.config['SECRET_KEY'] \
    or (app.config['SECRET_KEY'] == 'dev_key' and not app.config['DEBUG']):
    raise Exception('Set your secret key.')


# Init cache.
if not app.config['DEBUG']:
    cache = MemcachedCache(app.config['MEMCACHED_URL'])
else:
    cache = BaseCache()


# Load debug toolbar.
if app.config['DEBUG']:
    try:
        from flask_debugtoolbar import DebugToolbarExtension
        toolbar = DebugToolbarExtension(app)
    except ImportError as e:
        import sys
        sys.stderr.write('Flask Debug Toolbar was NOT loaded. Error: %s\n' % e)


from .admin import admin
from .views import core, api, auth
app.register_blueprint(core.bl)
app.register_blueprint(api.bl, url_prefix='/api')
app.register_blueprint(auth.bl)
from . import template_filters
from . import context_processors
