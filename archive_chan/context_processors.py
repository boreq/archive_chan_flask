"""
    Context processors are used to automatically inject variables and functions
    into the template context.
"""


import copy
import urllib
from flask import Blueprint
from flask.ext.login import current_user
from .lib.helpers import utc_now


bl = Blueprint('context_processors', __name__)


@bl.app_context_processor
def now():
    """Injects current time."""
    return dict(now=utc_now())


@bl.app_context_processor
def user():
    """Injects the object used by flask-login extension to represent
    the current user.
    """
    return dict(user=current_user)


@bl.app_context_processor
def board_url_query():
    """Injects method used to build the query part of the board url."""
    def url_query(parameters, name=None, value=None):
        parameters = copy.copy(parameters)
        if name:
            parameters[name] = value

        query =  '?sort=%s&saved=%s&last_reply=%s&tagged=%s' % (
            parameters['sort_with_operator'],
            parameters['saved'],
            parameters['last_reply'],
            parameters['tagged'],
        )

        if parameters['tag'] is not None:
            query += '&tag=%s' % (
                urllib.parse.quote('+'.join(parameters['tag']))
            )

        return query

    return dict(board_url_query=url_query)
