import datetime
import pytz
from flask.ext.login import current_user
from . import bl

@bl.app_context_processor
def now():
    return dict(now=pytz.utc.localize(datetime.datetime.utcnow()))

@bl.app_context_processor
def user():
    return dict(user=current_user)
