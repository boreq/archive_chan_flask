"""
    Implementes methods related to user authentication.
    flask-login extension provides basic functionality.
    Bcrypt is used instead of default Werkzeug hash implementation.
"""


from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager, login_user, logout_user
from .models import User


login_manager = LoginManager()
bcrypt = Bcrypt()


@login_manager.user_loader
def load_user(user_id):
    """Loads the User object based on the given id. Required by
    flask-login extension.
    """
    return User.query.get(user_id)


def login(username, password, remember=False):
    """Logs in the user. Returns True on sucess and False on failure
    (invalid username/password).
    """
    if not username or not password:
        return False

    # Get the User object.
    user = User.query.filter(User.username==username).first()
    if user is None:
        return False

    # Check if the password is correct.
    password_correct  = bcrypt.check_password_hash(user.password, password)
    if not password_correct:
        return False

    login_user(user, remember=remember)
    return True


def logout():
    """Logs out the user. Will not fail if the user is not logged in."""
    logout_user()
    return True
