from flask import Blueprint, current_app, send_from_directory


bl = Blueprint('files', __name__)


@bl.route('/media/<path:filename>')
def media(filename):
    return send_from_directory(current_app.config['MEDIA_ROOT'], filename)
