import datetime
import pytz
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

