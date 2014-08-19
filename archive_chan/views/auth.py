from flask import Blueprint, request, render_template, flash, redirect, url_for
from .. import auth


bl = Blueprint('auth', __name__)


@bl.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if auth.login(username, password):
            flash('Successfully logged in')
            return redirect(url_for('core.index'))
        else:
            flash('Invalid username or password')
    return render_template('auth/login.html')


@bl.route('/logout/')
def logout():
    auth.logout_user()
    flash('Logged out')
    return redirect(url_for('core.index'))
