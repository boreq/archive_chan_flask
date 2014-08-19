from . import api, auth, core, errors, files


def register_blueprints(app):
    app.register_blueprint(api.bl, url_prefix='/api')
    app.register_blueprint(auth.bl)
    app.register_blueprint(core.bl)
    app.register_blueprint(errors.bl)
    app.register_blueprint(files.bl)
