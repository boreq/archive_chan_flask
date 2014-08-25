import getpass
from flask.ext import script
from ..auth import generate_password_hash
from ..database import db
from ..models import User


class Command(script.Command):
    """Creates a new user. Should be used to create first user account in order
    to access the admin panel. 
    """

    def run(self):
        username = input('Username: ')
        password1 = getpass.getpass('Password: ')
        password2 = getpass.getpass('Confirm password: ')

        if password1 != password2:
            raise ValueError('Passwords did not match.')

        password1 = generate_password_hash(password1)

        user = User(username=username, password=password1)
        db.session.add(user)
        db.session.commit()
