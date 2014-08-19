from flask import Flask
from werkzeug.contrib.cache import MemcachedCache, BaseCache


cache = None


def create_app(config=None):
    app = Flask(__name__)

    # Load config.
    app.config.from_object('archive_chan.settings')
    app.config.from_envvar('ARCHIVE_CHAN_SETTINGS', True)
    if config is not None:
        app.config.update(config)

    # Check if the SECRET_KEY has been changed.
    if not (app.config['DEBUG'] or app.config['TESTING']) \
        and app.config['SECRET_KEY'] in ['', 'dev_key']:
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

    init_app(app)

    from . import views
    views.register_blueprints(app)

    from . import template_filters
    from . import context_processors
    app.register_blueprint(template_filters.bl)
    app.register_blueprint(context_processors.bl)

    return app


def init_app(app):
    from .database import db
    from .admin import admin
    from .auth import login_manager, bcrypt

    db.init_app(app)
    db.app = app
    admin.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
