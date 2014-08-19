"""
    Implements basic database related methods. flask-sqlalchemy extension
    provides database support. It is preferred over raw SQLAlchemy because
    it automatically handles the session management and binds it to request
    context. Actual database models are defined in models module.
"""


from flask.ext.sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def init_db():
    """Create all defined database tables."""
    db.create_all()


def destroy_db():
    """Drop all defined database tables."""
    db.drop_all()
