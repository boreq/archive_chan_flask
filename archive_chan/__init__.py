from flask import Flask


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

    validate_config(app)
    load_debug_toolbar(app)
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
    from . import cache
    db.init_app(app)
    admin.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    cache.init_app(app)


def validate_config(app):
    """Validates app config."""
    # Working in deployment mode (debug and testing disabled).
    if not (app.config['DEBUG'] or app.config['TESTING']):
        if app.config['SECRET_KEY'] in ['', 'dev_key']:
            raise Exception('Set your secret key.')


def load_debug_toolbar(app):
    """Loads the debug toolbar if possible."""
    if app.config['DEBUG']:
        try:
            from flask_debugtoolbar import DebugToolbarExtension
            toolbar = DebugToolbarExtension(app)
        except ImportError as e:
            import sys
            sys.stderr.write('Flask Debug Toolbar was not loaded. You can install it with `pip install flask-debugtoolbar`.\nError: %s\n' % e)
