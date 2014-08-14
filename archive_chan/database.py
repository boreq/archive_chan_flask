"""
    Implements basic database related methods.
    flask-sqlalchemy extension provides database support.
"""


from flask.ext.sqlalchemy import SQLAlchemy
from . import app


db = SQLAlchemy(app)


def init_db():
    """Create all defined database tables."""
    db.create_all()


def destroy_db():
    """Drop all defined database tables."""
    db.drop_all()
