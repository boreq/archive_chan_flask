from flask import Blueprint, request, render_template, flash, redirect, url_for
from .. import app, auth


bl = Blueprint('auth', __name__)


def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if auth.login(username, password):
            flash('Successfully logged in')
            return redirect(url_for('.index'))
        else:
            flash('Invalid username or password')
    return render_template('auth/login.html')


def logout():
    auth.logout_user()
    flash('Logged out')
    return redirect(url_for('.index'))


bl.add_url_rule('/login/', 'login', view_func=login, methods=('GET', 'POST'))
bl.add_url_rule('/logout/', 'logout', view_func=logout)
