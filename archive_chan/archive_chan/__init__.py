from flask import Blueprint

bl = Blueprint('archive_chan', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/archive_chan'
)

from . import urls
from . import template_filters
from . import context_processors
