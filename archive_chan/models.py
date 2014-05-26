from django.db import models


class Board(models.Model):
    name = models.CharField(max_length=255, primary_key = True)
    active = models.BooleanField(
        default=True,
        help_text='Should this board be updated with new posts?'
    )
    store_threads_for = models.IntegerField(
        default=48,
        help_text='[hours] After that much time passes from the last reply in a NOT SAVED thread it will be deleted. Set to 0 to preserve threads forever.'
    )
    replies_threshold = models.IntegerField(
        default=20,
        help_text='Store threads after they reach that many replies.'
    )

    def __str__(self):
        return format("/%s/" % self.name)


class Thread(models.Model):
    board = models.ForeignKey('Board')
    number = models.IntegerField()
    saved = models.BooleanField(default=False) # Threads which are not saved will get deleted after some time.
    auto_saved = models.BooleanField(default=False) # Was this thread saved automatically by a trigger?
    tags = models.ManyToManyField('Tag', through='TagToThread')

    class Meta:
        unique_together = ('board', 'number')

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


    # Used by board template. Can't figure out a query which wouldd fetch everything in one go.
    def first_post(self):
        return self.post_set.select_related('image').first()

    def __str__(self):
        return format("#%s" % (self.number))


class Post(models.Model):
    thread = models.ForeignKey('Thread')

    number = models.IntegerField()
    time = models.DateTimeField()

    name = models.CharField(max_length=255, blank=True)
    trip = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)

    subject = models.TextField(blank=True)
    comment = models.TextField(blank=True)

    save_time = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return format("#%s" % (self.number))


class Image(models.Model):
    original_name = models.CharField(max_length=255)
    post = models.OneToOneField('Post')
    image = models.FileField(upload_to = "post_images") # It is impossible to use ImageField to store webm.
    thumbnail = models.FileField(upload_to = "post_thumbnails")


class Trigger(models.Model):
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
    
    field = models.CharField(max_length=10, choices=FIELD_CHOICES)
    event = models.CharField(max_length=10, choices=EVENT_CHOICES)
    phrase = models.CharField(max_length=255, blank=True)
    case_sensitive = models.BooleanField(default=True)
    post_type = models.CharField(max_length=10, choices=POST_TYPE_CHOICES)

    save_thread = models.BooleanField(default=False, help_text='Save the thread.')
    tag_thread = models.ForeignKey('Tag', blank=True, null=True, default=None, help_text='Add this tag to the thread.')

    active = models.BooleanField(default=True)


class TagToThread(models.Model):
    thread = models.ForeignKey('Thread')
    tag = models.ForeignKey('Tag')
    automatically_added = models.BooleanField(default=False, editable=False)
    save_time = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return format('%s - %s' % (self.thread, self.tag))


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

# Delete downloaded images from the HDD when deleting a record.
@receiver(pre_delete, sender=Image)
def image_delete(sender, instance, **kwargs):
    instance.image.delete(False)
    instance.thumbnail.delete(False)
