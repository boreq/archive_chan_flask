"""
    Implementes methods related to user authentication.

    Basic functionality is provided by flask-login.
    Bcrypt provided by flask-bcrypt is used instead of default Werkzeug hash
    implementation.
"""


from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager, login_user, logout_user
from . import app
from .models import User


login_manager = LoginManager(app)
bcrypt = Bcrypt(app)


@login_manager.user_loader
def load_user(user_id):
    """Loads the User object based on the given id. Required by
    flask-login extension.
    """
    return User.query.get(user_id)


def login(username, password, remember=False):
    """Logs in the user. Returns True on success and False on failure
    (invalid username/password).
    """
    if not username or not password:
        return False

    # Get the User object.
    user = User.query.filter(User.username==username).first()
    if user is None:
        return False

    # Check if the password is correct.
    password_correct = check_password_hash(user.password, password)
    if not password_correct:
        return False

    login_user(user, remember=remember)
    return True


def logout():
    """Logs out the user. Will not fail if the user is not logged in."""
    logout_user()
    return True


def generate_password_hash(password):
    """Generates the password hash."""
    return bcrypt.generate_password_hash(password)


def check_password_hash(password_hash, password):
    """Checks if the password hash matches the password."""
    return bcrypt.check_password_hash(password_hash, password)
