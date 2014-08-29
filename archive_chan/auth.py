"""
    Implementes methods related to user authentication.

    Core functionality is provided by flask-login extension. Bcrypt provided by
    flask-bcrypt extension is used instead of the default password hashing
    implementation introduced in Werkzeug.
"""


from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager, login_user, logout_user
from .models import User


login_manager = LoginManager(add_context_processor=False)
bcrypt = Bcrypt()


@login_manager.user_loader
def load_user(user_id):
    """Returns an object used to represent a user. Required by flask-login
    extension.
    """
    return User.query.get(user_id)


def login(username, password, remember=False):
    """Logs in the user. Returns True on success or False on failure (in case of
    invalid username or password).

    username: String containing an username.
    password: String containing a password.
    remember: Bool indicating whether the user should be remembered after his
              session expires.
    """
    if not username or not password:
        return False

    user = User.query.filter(User.username==username).first()
    if user is None:
        return False

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
