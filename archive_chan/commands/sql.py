from inspect import isclass
from flask.ext import script
from sqlalchemy import schema
from .. import create_app, models
from ..database import db

class Command(script.Command):
    """Displays CREATE TABLE SQL statement for all models."""

    def run(self):
        for attr_name in dir(models):
            attr = getattr(models, attr_name)
            if isclass(attr) and issubclass(attr, db.Model):
                print(schema.CreateTable(attr.__table__).compile(db.engine))
