from flask import request, render_template, flash, redirect, url_for
from .. import auth


def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if auth.login(username, password):
            flash('Successfully logged in')
            return redirect(url_for('.index'))
        else:
            flash('Invalid username or password')
    return render_template('archive_chan/auth_login.html')


def logout():
    auth.logout_user()
    flash('Logged out')
    return redirect(url_for('.index'))
