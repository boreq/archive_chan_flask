from sqlalchemy.orm import exc
from flask import abort

def get_object_or_404(model, *criterion):
    try:
        return model.query.filter(*criterion).one()
    except (exc.NoResultFound, exc.MultipleResultsFound):
        abort(404)
