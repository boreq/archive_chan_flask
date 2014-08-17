"""
    Model views for flask-admin.
"""


from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.login import current_user
from wtforms import PasswordField, SelectField
from . import models, app
from .auth import generate_password_hash
from .database import db


admin = Admin(app, name='Archive Chan')


class CustomModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated()

    def __init__(self, session, **kwargs):
        super(CustomModelView, self).__init__(self.model, session, **kwargs)


class BoardView(CustomModelView):
    model = models.Board
    form_create_rules = ('active', 'store_threads_for', 'replies_threshold')
    column_list = ('name', 'active', 'store_threads_for', 'replies_threshold')
    form_excluded_columns = ('updates', 'threads',)


class UserView(CustomModelView):
    model = models.User
    form_excluded_columns = ('password',)
    column_list = ('username',)

    def scaffold_form(self):
        form_class = super(UserView, self).scaffold_form()
        form_class.new_password1 = PasswordField('New password')
        form_class.new_password2 = PasswordField('Confirm password')
        return form_class

    def on_model_change(self, form, model):
        if len(model.new_password1):
            if model.new_password1 != model.new_password2:
                raise ValueError('Passwords differ')
            model.password = generate_password_hash(form.new_password1.data)


class TagView(CustomModelView):
    model = models.Tag
    form_excluded_columns = ('tagtothread',)


class TriggerView(CustomModelView):
    model = models.Trigger
    form_excluded_columns = ('tagtothread',)
    form_overrides = {
        'field': SelectField,
        'event': SelectField,
        'post_type': SelectField,
    }
    form_args = {
        'field': {
            'choices': models.Trigger.FIELD_CHOICES
        },
        'event': {
            'choices': models.Trigger.EVENT_CHOICES
        },
        'post_type': {
            'choices': models.Trigger.POST_TYPE_CHOICES
        },
    }


class ThreadView(CustomModelView):
    model = models.Thread


admin.add_view(BoardView(db.session))
admin.add_view(UserView(db.session))
admin.add_view(TagView(db.session))
admin.add_view(TriggerView(db.session))

if app.config['DEBUG']:
    admin.add_view(ThreadView(db.session))
