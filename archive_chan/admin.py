from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from wtforms import PasswordField, SelectField
from . import models, app
from .auth import generate_password_hash
from .database import db


admin = Admin(app, name='Archive Chan')


class BoardView(ModelView):
    form_create_rules = ('active', 'store_threads_for', 'replies_threshold')
    column_list = ('name', 'active', 'store_threads_for', 'replies_threshold')
    form_excluded_columns = ('updates', 'threads',)

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
            model.password = generate_password_hash(form.new_password1.data)


class TagView(ModelView):
    form_excluded_columns = ('tagtothread',)

    def __init__(self, session, **kwargs):
        super(TagView, self).__init__(models.Tag, session, **kwargs)


class TriggerView(ModelView):
    form_excluded_columns = ('tagtothread',)
    form_overrides = {
        'field': SelectField,
        'event': SelectField,
        'post_type': SelectField,
    }
    form_args = dict(
        field=dict(
            choices=models.Trigger.FIELD_CHOICES
        ),
        event=dict(
            choices=models.Trigger.EVENT_CHOICES
        ),
        post_type=dict(
            choices=models.Trigger.POST_TYPE_CHOICES
        )
    )

    def __init__(self, session, **kwargs):
        super(TriggerView, self).__init__(models.Trigger, session, **kwargs)


class ThreadView(ModelView):
    def __init__(self, session, **kwargs):
        super(ThreadView, self).__init__(models.Thread, session, **kwargs)


admin.add_view(BoardView(db.session))
admin.add_view(UserView(db.session))
admin.add_view(TagView(db.session))
admin.add_view(TriggerView(db.session))

if app.config['DEBUG']:
    admin.add_view(ThreadView(db.session))
