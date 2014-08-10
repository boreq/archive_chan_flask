"""
    Implements basic database related methods.
    flask-sqlalchemy extension provides database support.
"""


from flask import current_app
from flask.ext.sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def init_db():
    """Create all defined database tables."""
    db.create_all()


def destroy_db():
    """Drop all defined database tables."""
    db.drop_all()
