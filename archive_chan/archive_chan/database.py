from flask import current_app
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db():
    db.create_all()

def destroy_db():
    db.drop_all()
