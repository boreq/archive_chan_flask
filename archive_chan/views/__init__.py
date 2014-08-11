from flask import send_from_directory, render_template
from .. import app

@app.route('/media/<path:filename>')
def media(filename):
    return send_from_directory(app.config['MEDIA_ROOT'], filename)


@app.errorhandler(404)
def error_404(e):
    print(e)
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def error_500(e):
    return render_template('errors/500.html'), 500
