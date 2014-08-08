import os
from flask import url_for
from .database import db

class Board(db.Model):
    __tablename__ = 'archive_chan_board'

    name = db.Column(db.String(255), primary_key=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    store_threads_for = db.Column(db.Integer, default=48, nullable=False)
    replies_threshold = db.Column(db.Integer, default=20, nullable=False)

    threads = db.relationship('Thread', cascade='all,delete', backref='board', lazy='dynamic')

    def __str__(self):
        return '/%s/' % self.name

    def get_absolute_url(self):
        return url_for('.board', board=self.name)


tag_to_thread = db.Table('archive_chan_tagtothread', 
    db.Column('thread_id', db.Integer, db.ForeignKey('archive_chan_thread.id'), nullable=False),
    db.Column('tag_id', db.Integer, db.ForeignKey('archive_chan_tag.id'), nullable=False),
    db.Column('automatically_added', db.Boolean,default=False, nullable=False),
    db.Column('save_time', db.DateTime(timezone=True), nullable=False)
)


class Tag(db.Model):
    __tablename__ = 'archive_chan_tag'
    __table_args__ = (
        db.UniqueConstraint('name', name='_name_uc'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

    def __str__(self):
        return self.name


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

    replies = db.Column(db.Integer, nullable=False, default=0)
    images = db.Column(db.Integer, nullable=False, default=0)
    first_reply = db.Column(db.DateTime(timezone=True), nullable=True, default=None)
    last_reply = db.Column(db.DateTime(timezone=True), nullable=True, default=None)

    posts = db.relationship('Post', cascade='all,delete', backref='thread', lazy='dynamic')
    tags = db.relationship(Tag, secondary=tag_to_thread, cascade='all,delete', backref='thread', lazy='dynamic')

    # Used by scraper.
    def last_reply_time(self):
        last = self.post_set.last()
        if last is None:
            return None
        else:
            return last.time

    # Used by scraper.
    def count_replies(self):
        return self.post_set.count() - 1

    # Used by board template.
    def first_post(self):
        return self.posts.order_by(Post.number).first()

    def __str__(self):
        return '#%s' % (self.number)

    def get_absolute_url(self):
        return url_for('.thread', board=self.board.name, thread=self.number)


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

    save_time = db.Column(db.DateTime(timezone=True), nullable=False)

    image = db.relationship('Image', cascade='all,delete', uselist=False, backref='post', lazy='joined')

    def is_main(self):
        return (self.number == self.thread.number)

    def __str__(self):
        return '#%s' % self.number

    def get_absolute_url(self):
        return '%s#post-%s' % (self.thread.get_absolute_url(), self.number)

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

    @property
    def image_url(self):
        return url_for('.media', filename=self.image)

    @property
    def thumbnail_url(self):
        return url_for('.media', filename=self.thumbnail)

    def get_extension(self):
        name, extension = os.path.splitext(self.image)
        return extension


class Trigger(db.Model):
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
    tag_id = db.Column(
        db.Integer,
        db.ForeignKey(Tag.id, deferrable=True, initially='DEFFERED'),
        nullable=True
    )

    active = db.Column(db.Boolean, nullable=False, default=True)

'''
class TagToThread(models.Model):
    thread = models.ForeignKey('Thread')
    tag = models.ForeignKey('Tag')
    automatically_added = models.BooleanField(default=False, editable=False)
    save_time = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return format('%s - %s' % (self.thread, self.tag))


class Update(models.Model):
    CURRENT = 0
    FAILED = 1
    COMPLETED = 2

    STATUS_CHOICES = (
        (CURRENT, 'Started'),
        (FAILED, 'Failed'),
        (COMPLETED, 'Completed'),
    )

    board = models.ForeignKey('Board')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=CURRENT)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True)

    used_threads = models.IntegerField()

    total_time = models.FloatField(default=0)
    wait_time = models.FloatField(default=0)
    download_time = models.FloatField(default=0)

    processed_threads = models.IntegerField(default=0)
    added_posts = models.IntegerField(default=0)
    removed_posts = models.IntegerField(default=0)

    downloaded_images = models.IntegerField(default=0)
    downloaded_thumbnails = models.IntegerField(default=0)
    downloaded_threads = models.IntegerField(default=0)

    class Meta:
        ordering = ['-start']

@receiver(pre_delete, sender=Image)
def pre_image_delete(sender, instance, **kwargs):
    """Delete images from the HDD."""
    instance.image.delete(False)
    instance.thumbnail.delete(False)

@receiver(post_save, sender=Image)
def post_image_save(sender, instance, created, **kwargs):
    """Update images."""
    if created:
        thread = instance.post.thread
        thread.images += 1
        thread.save()

@receiver(post_save, sender=Post)
def post_post_save(sender, instance, created, **kwargs):
    """Update the replies, last_reply and first_reply."""
    if created:
        thread = instance.thread

        # Replies.
        thread.replies += 1

        # Last reply.
        if thread.last_reply is None or instance.time > thread.last_reply:
            thread.last_reply = instance.time

        # First reply.
        if thread.first_reply is None or instance.time < thread.first_reply:
            thread.first_reply = instance.time

        thread.save()

@receiver(post_delete, sender=Post)
def post_post_delete(sender, instance, **kwargs):
    """Update replies, images, last_reply, first_reply."""
    thread = instance.thread

    # Replies
    thread.replies -= 1

    # Images.
    try:
        if instance.image:
            thread.images -= 1

    except:
        pass

    # First and last reply.
    if thread.first_reply == instance.time or thread.last_reply == instance.time:
        thread_recount = Thread.objects.annotate(
            min_post=Min('post__time'),
            max_post=Max('post__time')
        ).get(pk=instance.thread.pk)
        
        thread.first_reply=thread_recount.min_post
        thread.last_reply=thread_recount.max_post

    thread.save()
'''
