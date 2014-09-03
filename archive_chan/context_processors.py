"""
    Context processors are used to automatically inject variables and functions
    into the template context. The context processors defined here are attached
    to a blueprint which is registered on an application in create_app method.
"""


from flask import Blueprint
from flask.ext.login import current_user
from .lib import helpers


bl = Blueprint('context_processors', __name__)


@bl.app_context_processor
def now():
    """Injects current time."""
    return dict(now=helpers.utc_now())


@bl.app_context_processor
def user():
    """Injects the object used by flask-login extension to represent the
    current user.
    """
    return dict(user=current_user)


@bl.app_context_processor
def url_queries():
    """Injects the methods used to build url queries."""
    return dict(    
        board_url_query=helpers.board_url_query,
        search_url_query=helpers.search_url_query
    )
