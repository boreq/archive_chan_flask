from flask import Blueprint, render_template


bl = Blueprint('errors', __name__)


@bl.app_errorhandler(404)
def error_404(e):
    return render_template('errors/404.html', body_id='body-error'), 404


@bl.app_errorhandler(500)
def error_500(e):
    return render_template('errors/500.html', body_id='body-error'), 500
