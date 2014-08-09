from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from wtforms import PasswordField
from . import models
from .auth import bcrypt
from .database import db

admin = Admin(name='Archive Chan')


class BoardView(ModelView):
    form_create_rules = ('active', 'store_threads_for', 'replies_threshold')
    column_list = ('name', 'active', 'store_threads_for', 'replies_threshold')

    def __init__(self, session, **kwargs):
        super(BoardView, self).__init__(models.Board, session, **kwargs)


class UserView(ModelView):
    form_excluded_columns = ('password',)
    column_list = ('username',)

    def __init__(self, session, **kwargs):
        super(UserView, self).__init__(models.User, session, **kwargs)

    def scaffold_form(self):
        form_class = super(UserView, self).scaffold_form()
        form_class.new_password1 = PasswordField('New password')
        form_class.new_password2 = PasswordField('Confirm password')
        return form_class

    def on_model_change(self, form, model):
        if len(model.new_password1):
            if model.new_password1 != model.new_password2:
                raise ValueError('Passwords differ')
            model.password = bcrypt.generate_password_hash(form.new_password1.data)


admin.add_view(BoardView(db.session))
admin.add_view(UserView(db.session))
