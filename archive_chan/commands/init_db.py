from flask.ext import script
from ..database import init_db


class Command(script.Command):
    """Creates all database tables."""

    def run(self):
        init_db()
