"""
    flask-sqlalchemy models.
"""


import os
from flask import url_for, current_app
from flask.ext.login import UserMixin
from werkzeug.utils import secure_filename
from sqlalchemy.ext.associationproxy import association_proxy
from .database import db
from .lib.helpers import utc_now


class User(UserMixin, db.Model):
    """User model and at the same time an user object used by flask-login."""

    __tablename__ = 'archive_chan_user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __str__(self):
        return self.username


class Board(db.Model):
    __tablename__ = 'archive_chan_board'

    name = db.Column(db.String(255), primary_key=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    store_threads_for = db.Column(db.Integer, default=48, nullable=False)
    replies_threshold = db.Column(db.Integer, default=20, nullable=False)

    threads = db.relationship('Thread',
        cascade='all,delete-orphan',
        backref=db.backref('board', lazy='joined'),
        lazy='dynamic'
    )
    updates = db.relationship('Update',
        cascade='all,delete-orphan',
        backref='board',
        lazy='dynamic'
    )

    @property
    def id(self):
        return self.name

    def __str__(self):
        return '/%s/' % self.name

    def get_absolute_url(self):
        return url_for('core.board', board=self.name)


class Thread(db.Model):
    __tablename__ = 'archive_chan_thread'
    __table_args__ = (
        db.UniqueConstraint('board_id', 'number', name='_board_thread_uc'),
    )

    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(
        db.String(255),
        db.ForeignKey(Board.name, deferrable=True, initially='DEFERRED'),
        nullable=False
    )
    number = db.Column(db.Integer, nullable=False)
    saved = db.Column(db.Boolean, nullable=False, default=False)
    auto_saved = db.Column(db.Boolean, nullable=False, default=False)

    replies = db.Column(db.Integer, nullable=False)
    images = db.Column(db.Integer, nullable=False)
    first_reply = db.Column(db.DateTime(timezone=True), nullable=True, default=None)
    last_reply = db.Column(db.DateTime(timezone=True), nullable=True, default=None)

    tags = association_proxy('tagtothread', 'tag')

    # An easy way to access the master post. Can be used in joins.
    first_post = db.relationship('Post',
        primaryjoin='and_(Thread.id==Post.thread_id, Thread.number==Post.number)',
        uselist=False
    )
    posts = db.relationship('Post',
        cascade='all,delete-orphan',
        backref=db.backref('thread', lazy='joined'),
        lazy='dynamic'
    )
    tagtothreads = db.relationship('TagToThread',
        cascade='all,delete-orphan',
        lazy='dynamic'
    )

    def __init__(self, **kwargs):
        """Default value of a db.Column is set too late, those values must be
        available earlier.
        """
        self.replies = kwargs.get('replies', 0)
        self.images = kwargs.get('images', 0)
        db.Model.__init__(self, **kwargs)

    def post_deleted(self):
        """Called when a post is deleted to update the properties."""
        self.replies -= 1

    def image_deleted(self):
        """Called when an image is deleted to update the properties."""
        self.images -= 1

    def count_replies(self):
        """Used by ThreadScraper to get the amount of replies which excludes
        the first post.
        """
        return self.replies - 1

    def old_first_post(self):
        """Used in the board template."""
        return self.posts.order_by(Post.number).first()

    def __str__(self):
        return '#%s' % (self.number)

    def get_absolute_url(self):
        return url_for('core.thread', board=self.board.name, thread=self.number)


class Post(db.Model):
    __tablename__ = 'archive_chan_post'

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(
        db.Integer,
        db.ForeignKey(Thread.id, deferrable=True, initially='DEFERRED'),
        nullable=False
    )

    number = db.Column(db.Integer, nullable=False)
    time = db.Column(db.DateTime(timezone=True), nullable=False)

    name = db.Column(db.String(255), nullable=False)
    trip = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(2), nullable=False)

    subject = db.Column(db.Text, nullable=False)
    comment = db.Column(db.Text, nullable=False)

    save_time = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now())

    image = db.relationship('Image',
        cascade='all,delete-orphan',
        uselist=False,
        backref='post',
        lazy='joined'
    )

    def __init__(self, **kwargs):
        """Constructor updates the denormalized data."""
        thread = kwargs['thread']
        thread.replies += 1

        if thread.last_reply is None or kwargs['time'] > thread.last_reply:
            thread.last_reply = kwargs['time']

        if thread.first_reply is None or kwargs['time'] < thread.first_reply:
            thread.first_reply = kwargs['time']

        db.Model.__init__(self, **kwargs)

    def is_main(self):
        return (self.number == self.thread.number)

    def __str__(self):
        return '#%s' % self.number

    def get_anchor(self):
        return '#post-%s' % self.number

    def get_absolute_url(self):
        return self.thread.get_absolute_url() + self.get_anchor()


class Image(db.Model):
    __tablename__ = 'archive_chan_image'

    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(255), nullable=False)
    post_id = db.Column(
        db.Integer,
        db.ForeignKey(Post.id, deferrable=True, initially='DEFERRED'),
        nullable=False
    )
    image = db.Column(db.String(255), nullable=False)
    thumbnail = db.Column(db.String(255), nullable=False)

    def __init__(self, **kwargs):
        """Constructor updates the denormalized data."""
        kwargs['post'].thread.images += 1
        db.Model.__init__(self, **kwargs)

    @property
    def image_url(self):
        return url_for('files.media', filename=self.image)

    @property
    def thumbnail_url(self):
        return url_for('files.media', filename=self.thumbnail)

    def save_image(self, file_storage, filename):
        filename = secure_filename(filename)
        path = os.path.join('post_images', filename)
        self.image = path
        path = os.path.join(current_app.config['MEDIA_ROOT'], path)
        file_storage.save(path)

    def save_thumbnail(self, file_storage, filename):
        filename = secure_filename(filename)
        path = os.path.join('post_thumbnails', filename)
        self.thumbnail = path
        path = os.path.join(current_app.config['MEDIA_ROOT'], path)
        file_storage.save(path)

    def delete_files(self):
        for filename in [self.image, self.thumbnail]:
            path = os.path.join(current_app.config['MEDIA_ROOT'], filename)
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def get_extension(self):
        name, extension = os.path.splitext(self.image)
        return extension


class Tag(db.Model):
    __tablename__ = 'archive_chan_tag'
    __table_args__ = (
        db.UniqueConstraint('name', name='_name_uc'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

    threads = association_proxy('tagtothread', 'thread')
    triggers = db.relationship('Trigger',
        cascade='all,delete-orphan',
        backref=db.backref('tag', lazy='joined'),
        lazy='dynamic'
    )

    def __str__(self):
        return self.name


class TagToThread(db.Model):
    __tablename__ = 'archive_chan_tagtothread'

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(
        db.Integer,
        db.ForeignKey(Thread.id, deferrable=True, initially='DEFERRED'),
        nullable=False
    )
    tag_id = db.Column(
        db.Integer,
        db.ForeignKey(Tag.id, deferrable=True, initially='DEFERRED'),
        nullable=False
    )
    automatically_added = db.Column(db.Boolean, nullable=False)
    save_time = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now())

    tag = db.relationship(Tag,
        backref='tagtothread',
        lazy='joined'
    )
    thread = db.relationship(Thread,
        backref='tagtothread'
    )

    def __init__(self, tag=None, thread=None, automatically_added=False, **kwargs):
        self.tag_id = getattr(tag, 'id', None)
        self.thread_id = getattr(thread, 'id', None)
        self.automatically_added = automatically_added
        self.save_time = utc_now()
        db.Model.__init__(self, **kwargs)

    def __str__(self):
        return '%s - %s' % (self.thread, self.tag)


class Trigger(db.Model):
    __tablename__ = 'archive_chan_trigger'

    FIELD_CHOICES = (
        ('name', 'Name'),
        ('trip', 'Trip'),
        ('email', 'Email'),
        ('subject', 'Subject'),
        ('comment', 'Comment'),
    )

    EVENT_CHOICES = (
        ('contains', 'Contains'),
        ('containsno', 'Doesn\'t contain'),
        ('is', 'Is'),
        ('isnot', 'Is not'),
        ('begins', 'Begins with'),
        ('ends', 'Ends with'),
    )

    POST_TYPE_CHOICES=(
        ('any', 'Any post'),
        ('master', 'First post'),
        ('sub', 'Reply'),
    )

    id = db.Column(db.Integer, primary_key=True)

    field = db.Column(db.String(10), nullable=False)
    event = db.Column(db.String(10), nullable=False)
    phrase = db.Column(db.String(255), nullable=False)
    case_sensitive = db.Column(db.Boolean, nullable=False, default=True)
    post_type = db.Column(db.String(10), nullable=False)

    save_thread = db.Column(db.Boolean, nullable=False, default=False)
    # [TODO] change legacy column name
    tag_id = db.Column(
        'tag_thread_id',
        db.Integer,
        db.ForeignKey(Tag.id, deferrable=True, initially='DEFERRED'),
        nullable=True
    )

    active = db.Column(db.Boolean, nullable=False, default=True)


class Update(db.Model):
    __tablename__ = 'archive_chan_update'

    CURRENT = 0
    FAILED = 1
    COMPLETED = 2

    STATUS_CHOICES = (
        (CURRENT, 'Started'),
        (FAILED, 'Failed'),
        (COMPLETED, 'Completed'),
    )

    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(
        db.String(255),
        db.ForeignKey(Board.name, deferrable=True, initially='DEFERRED'),
        nullable=False
    )

    status = db.Column(db.SmallInteger, nullable=False, default=CURRENT)
    start = db.Column(db.DateTime(timezone=True), nullable=False)
    end = db.Column(db.DateTime(timezone=True), nullable=True)

    used_threads = db.Column(db.Integer, nullable=False)

    total_time = db.Column(db.Float, nullable=False, default=0)
    wait_time = db.Column(db.Float, nullable=False, default=0)
    download_time = db.Column(db.Float, nullable=False, default=0)

    processed_threads = db.Column(db.Integer, nullable=False, default=0)
    added_posts = db.Column(db.Integer, nullable=False, default=0)
    removed_posts = db.Column(db.Integer, nullable=False, default=0)

    downloaded_images = db.Column(db.Integer, nullable=False, default=0)
    downloaded_thumbnails = db.Column(db.Integer, nullable=False, default=0)
    downloaded_threads = db.Column(db.Integer, nullable=False, default=0)

    def get_status_display(self):
        return dict(self.STATUS_CHOICES)[self.status]


def pre_image_delete(mapper, connection, target):
    """Delete the files stored on HDD while deleting the database record."""
    target.delete_files()
db.event.listen(Image, 'before_delete', pre_image_delete)
