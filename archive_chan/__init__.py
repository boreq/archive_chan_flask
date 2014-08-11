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

# Init debug toolbar.
if app.config['DEBUG']:
    try:
        from flask_debugtoolbar import DebugToolbarExtension
        if not app.config.get('SECRET_KEY'):
            # I don't know a better way to get random data.
            app.config['SECRET_KEY'] = 'LOLOLOLOLOLOLOLOLOL'
        toolbar = DebugToolbarExtension(app)
    except ImportError as e:
        import sys
        sys.stderr.write('Flask Debug Toolbar was NOT loaded. Error: %s\n' % e)

from .database import db
from .admin import admin
from .auth import login_manager, bcrypt
db.init_app(app)
admin.init_app(app)
login_manager.init_app(app)
bcrypt.init_app(app)

from .views import core, api, auth
app.register_blueprint(core.bl)
app.register_blueprint(api.bl, url_prefix='/api')
app.register_blueprint(auth.bl)

from . import template_filters
from . import context_processors
