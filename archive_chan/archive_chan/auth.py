from flask.ext.login import LoginManager
from flask.ext.bcrypt import Bcrypt

login_manager = LoginManager()
bcrypt = Bcrypt()

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
