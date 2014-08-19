from flask import Flask
from werkzeug.contrib.cache import MemcachedCache, BaseCache


cache = None


def create_app(config=None, envvar='ARCHIVE_CHAN_SETTINGS'):
    """Application factory. Thanks to this pattern it is possible to load
    different settings during unit testing or while deploying multiple
    instances of the archive.

    config: values defined in this config will override the ones defined in
            other config files. This can ba a dict or flask.Config object.
    envvar: name of the environment variable containing the path to the
            config file which will be loaded.

    Config loading order (the configuration keys defined in previous configs
    are overriden by those defined later):
    1. settings.py (default configuration)
    2. configuration with path set in envvar
    3. configuration passed as config parameter
    """
    app = Flask(__name__)

    # Load config.
    app.config.from_object('archive_chan.settings')
    app.config.from_envvar(envvar, True)
    if config is not None:
        app.config.update(config)

    # Deployment version/debug or testing.
    if not (app.config['DEBUG'] or app.config['TESTING']):
        if app.config['SECRET_KEY'] in ['', 'dev_key']:
            raise Exception('Set your secret key.')
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
            sys.stderr.write('Flask Debug Toolbar was not loaded. Error: %s\n' % e)

    init_app(app)

    from . import views
    views.register_blueprints(app)

    from . import template_filters
    from . import context_processors
    app.register_blueprint(template_filters.bl)
    app.register_blueprint(context_processors.bl)

    return app


def init_app(app):
    """Calls init_app on all used extensions."""
    from .database import db
    from .admin import admin
    from .auth import login_manager, bcrypt

    db.init_app(app)
    # I am not sure why db.app isn't set automatically. It happens if the app
    # object is passed directly to the constructor but not if the init_app
    # method is called later.
    db.app = app
    admin.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
