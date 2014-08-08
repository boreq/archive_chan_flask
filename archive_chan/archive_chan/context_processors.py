import datetime
import pytz
from . import bl

@bl.app_context_processor
def now():
    return dict(now=pytz.utc.localize(datetime.datetime.utcnow()))
