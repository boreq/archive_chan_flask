import copy
import datetime
import pytz
import urllib
from sqlalchemy.orm import exc
from flask import abort


def get_object_or_404(model, *criterion):
    try:
        return model.query.filter(*criterion).one()
    except (exc.NoResultFound, exc.MultipleResultsFound):
        abort(404)


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.flush()
        session.refresh(instance)
        return instance, True


def utc_now():
    """Get a datetime representing current time in UTC."""
    return pytz.utc.localize(datetime.datetime.utcnow())


def timestamp_to_datetime(timestamp):
    """Convert UNIX timestamp (seconds from epoch in UTC) to Python datetime
    in UTC.
    """
    return datetime.datetime.fromtimestamp(timestamp, pytz.utc)


def board_url_query(parameters, name=None, value=None):
    """Constructs the query part of the board url.

    parameters: dict with values of the parameters.
    name: name of a parameter to which a new value will be assigned.
    value: new value of a parameter.
    """
    parameters = copy.copy(parameters)
    if name:
        parameters[name] = value
    query = '?sort=%s&saved=%s&last_reply=%s&tagged=%s' % (
        parameters['sort_with_operator'],
        parameters['saved'],
        parameters['last_reply'],
        parameters['tagged'],
    )
    if parameters['tag'] is not None:
        tags = urllib.parse.quote('+'.join(parameters['tag']))
        query += '&tag=%s' % tags
    return query


def search_url_query(parameters, name=None, value=None):
    """Constructs the query part of the search url. Parameters like
    board_url_query.
    """
    parameters = copy.copy(parameters)
    if name:
        parameters[name] = value
    query = '?saved=%s&type=%s&created=%s&search=%s' % (
        parameters['saved'],
        parameters['type'],
        parameters['created'],
        parameters['search']
    )
    return query
