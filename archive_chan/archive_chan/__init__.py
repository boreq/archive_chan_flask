from flask import Blueprint

bl = Blueprint('archive_chan', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/archive_chan'
)

def init_app(app):
    from .database import db
    from .admin import admin
    from .auth import login_manager, bcrypt
    db.init_app(app)
    admin.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

from . import urls
from . import template_filters
from . import context_processors
