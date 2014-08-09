from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager, login_user, logout_user
from .models import User

login_manager = LoginManager()
bcrypt = Bcrypt()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def login(username, password, remember=False):
    if not username or not password:
        return False

    user = User.query.filter(User.username==username).first()
    if user is None:
        return False

    password_correct  = bcrypt.check_password_hash(user.password, password)
    if not password_correct:
        return False

    login_user(user, remember=remember)
    return True

def logout():
    logout_user()
    return True
