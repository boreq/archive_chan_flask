import requests, datetime, re, time, html, sys
from archive_chan.models import Thread, Post, Image, Trigger, TagToThread
from django.utils.timezone import utc
from django.db import transaction

from django.core.files.base import ContentFile

from archive_chan.settings import AppSettings

class ScrapError(Exception):
    """Error created only because it allows to pass a message."""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class ThreadInfo:
    """Class used for storing information about the thread."""

    def __init__(self, thread_json): 
        """Constructor loads the data from a part of the JSON retrieved from the catalog API."""

        # Get the thread number.
        self.number = thread_json['no']
        
        # Get the time of the last reply or thread creation time.
        if 'last_replies' in thread_json and len(thread_json) > 0:
            last_reply_time = int(thread_json['last_replies'][-1]['time'])
        else:
            last_reply_time = int(thread_json['time'])

        self.last_reply_time = datetime.datetime.fromtimestamp(last_reply_time).replace(tzinfo=utc) # Note the time-zone-aware datetime.

        # Get the number of the replies in the thread (first post doest not count - it is considered as a thread).
        self.replies = int(thread_json['replies'])


class PostData:
    """Class used for storing data about the post before saving it to the databse."""

    def replace_content(self, text):
        """Cleans the HTML from the post comment. Returns a string."""

        # Remove >>quotes.
        text = re.sub(r'\<a.*?class="quotelink".*?\>(.*?)\</a\>', r"\1", text)

        # Remove spans: >le meme arrows/deadlinks etc.
        text = re.sub(r'\<span.*?\>(.*?)\</span\>', r"\1", text)

        # Code.
        text = re.sub(r'\<pre.*?\>(.*?)\</pre\>', r"[code]\1[/code]", text)

        # Newline.
        text = text.replace("<br>", "\n")

        # Word break opportunity.
        text = text.replace("<wbr>", "")

        # Unescape characters.
        text = html.unescape(text)

        return text


    def __init__(self, post_json): 
        """Constructor loads the data from JSON retrieved from the thread API."""

        self.number = int(post_json['no'])
        self.time = datetime.datetime.fromtimestamp(int(post_json['time'])).replace(tzinfo=utc)

        self.name = post_json.get('name', "")
        self.trip = post_json.get('trip', "")
        self.email = post_json.get('email', "")

        self.subject = self.replace_content(post_json.get('sub', ""))
        self.comment = self.replace_content(post_json.get('com', ""))

        self.filename = post_json.get('tim')
        self.extension = post_json.get('ext')
        self.original_filename = post_json.get('filename')

class Triggers:
    """Class handling triggers."""

    def __init__(self):
        # Prepare trigger list.
        self.triggers = Trigger.objects.filter(active=True)

    def check_post_type(self, trigger, thread, post_data):
        """True if type of the post is correct, false otherwise."""
        # Sub post and we are looking for the master.
        if post_data.number != thread.number and trigger.post_type == 'master':
            return False

        # Master post and we are looking for the sub.
        if post_data.number == thread.number and trigger.post_type == 'sub':
            return False

        return True
    
    def check_event(self, trigger, post_data):
        """True if event terms are fulfilled, false otherwise."""
        field_value = str(getattr(post_data, trigger.field))
        trigger_value = trigger.phrase

        # Case insensitive?
        if not trigger.case_sensitive:
            field_value = field_value.lower()
            trigger_value = trigger_value.lower()

        # Check if the event occurs.
            if trigger.event == 'isnot' or trigger.event == 'containsno':
                return_value = False
            else:
                return_value = True

        if trigger.event == 'contains' or trigger.event == 'containsno':
            if field_value.find(trigger_value) >= 0:
                return return_value
            else:
                return not return_value

        if trigger.event == 'is' or trigger.event == 'isnot':
            if field_value == trigger_value:
                return return_value
            else:
                return not return_value

        if trigger.event == 'begins':
            return field_value.startswith(trigger_value)

        if trigger.event == 'ends':
            return field_value.endsswith(trigger_value)

        return False


    def get_actions(self, trigger, thread, post_data):
        """Returns a set of actions to execute."""
        if not self.check_post_type(trigger, thread, post_data):
            return None
        
        actions = set()

        if self.check_event(trigger, post_data):
            if trigger.save_thread:
                actions.add(('save', 0))

            if trigger.tag_thread is not None:
                actions.add(('add_tag', trigger.tag_thread))

        return actions

    def handle(self, post_data, thread):
        
        actions = set()

        for trigger in self.triggers:
            new_actions = self.get_actions(trigger, thread, post_data)

            if not new_actions is None:
                actions = actions | new_actions

        for action in actions:
            if action[0] == 'save' and not thread.saved:
                thread.saved = True
                thread.auto_saved = True
                thread.save()

            if action[0] == 'add_tag':
                if not TagToThread.objects.filter(thread=thread, tag=action[1]).exists():
                    tag_to_thread = TagToThread(thread=thread, tag=action[1], automatically_added=True)
                    tag_to_thread.save()


class Scraper:
    """Class is used for downloading the data from the API and saving it in the database."""

    def __init__(self, board, **kwargs):
        """Board is a database object, not a board name.
        Accepted kwargs: bool progress
        """

        self.board = board

        self.last_api_request = None
        self.last_file_request = None

        if 'progress' in kwargs:
            self.show_progress = kwargs['progress']
        else:
            self.show_progress = False

        self.triggers = Triggers()

        # Info counters.
        self.total_wait = 0
        self.total_download_time = 0

        self.processed_threads = 0
        self.added_posts = 0
        self.removed_posts = 0

        self.downloaded_images = 0
        self.downloaded_thumbnails = 0
        self.downloaded_threads = 0

    def wait(self, time_beetwen_requests, last_request):
        """Wait to make sure that at least time_beetwen_requests passed since last_request."""
        # Convert seconds to microseconds.
        time_beetwen_requests *= 1000000

        # Check when was the last request performed and wait if necessary.
        if not last_request is None:
            time_passed = datetime.datetime.now() - last_request

            # If not enough time passed since the last request wait for the remaining time.
            if time_passed.microseconds < time_beetwen_requests:
                # Calculate remaining time and convert microseconds to seconds.
                wait_for_seconds = (time_beetwen_requests - time_passed.microseconds) / 1000000
                self.total_wait += wait_for_seconds
                time.sleep(wait_for_seconds)

    def api_wait(self):
        """Wait in order to satisfy the API rules."""
        self.wait(AppSettings.get('API_WAIT'), self.last_api_request)

        # Store this request time.
        self.last_api_request = datetime.datetime.now()


    def file_wait(self):
        """Wait in order to satisfy the rules. Used before downloading images."""
        self.wait(AppSettings.get('FILE_WAIT'), self.last_file_request)

        # Store this request time.
        self.last_file_request = datetime.datetime.now()


    def get_url(self, url):
        """Download data from an url."""
        # download_start and similar variables are used only for generating statistics.
        download_start = datetime.datetime.now()

        data = requests.get(url, timeout=AppSettings.get('CONNECTION_TIMEOUT'))

        download_time = datetime.datetime.now() - download_start
        self.total_download_time += download_time.seconds

        return data


    def get_catalog_json(self):
        """Get the catalog data from an official API."""
        url = format("https://a.4cdn.org/%s/catalog.json" % (self.board.name))
        self.api_wait()
        return self.get_url(url).json()


    def get_thread_json(self, thread_number):
        """Get the thread data from an official API."""
        url = format("https://a.4cdn.org/%s/thread/%s.json" % (self.board.name, thread_number))
        self.api_wait()
        self.downloaded_threads += 1 
        return self.get_url(url).json()


    def get_image(self, filename, extension):
        """Download an image."""
        url = format("https://i.4cdn.org/%s/%s%s" % (self.board.name, filename, extension))
        self.file_wait()
        self.downloaded_images += 1 
        return self.get_url(url).content


    def get_thumbnail(self, filename):
        """Download a thumbnail."""
        url = format("https://t.4cdn.org/%s/%ss.jpg" % (self.board.name, filename))
        self.file_wait()
        self.downloaded_thumbnails += 1 
        return self.get_url(url).content


    def handle_thread(self, thread_json):
        """Download/update the thread if necessary."""
        thread_info = ThreadInfo(thread_json)

        # Download only above certain number of posts.
        # (seriously it is wise do let the moderators do their job first)
        if thread_info.replies < self.board.replies_threshold:
            return

        # Get the exisiting entry for this thread from the database or create a new record for it.
        try:
            thread = Thread.objects.filter(board=self.board).get(number=thread_info.number)

            # Should the thread be updated?
            # Check only if there is any data about the thread
            # (the download of the first post was successful).
            if not thread.last_reply_time() is None and thread.post_set.count() > 0:
                # It has to have newer replies or different number of replies.
                # Note: use count_replies because 4chan does not count the first post as a reply.
                if thread_info.last_reply_time <= thread.last_reply_time() and thread_info.replies == thread.count_replies():
                    return

        except Thread.DoesNotExist:
            thread = Thread(board=self.board, number=thread_info.number)

        # Get the last saved post in this thread.
        last_post = thread.post_set.order_by('number').last()

        # Determine the last post's number or pick an imaginary one.
        # Only posts with a number above this one will be added to the database.
        if last_post is None:
            last_post_number = -1;
        else:
            last_post_number = last_post.number;

        # Download the thread data.
        try:
            thread_json = self.get_thread_json(thread_info.number)

        except:
            # Could not update the thread and there are no posts in the saved one.
            # That means that something got corrupted. Remove it because it might not exist anymore.
            if not thread is None and thread.pk and thread.post_set.count() == 0:
                thread.delete()

            raise ScrapError('Unable to download thread data. It might not exist anymore.')

        # Do not save earlier or you might end up with a thread without posts after a download error.
        if not thread.pk:
            thread.save()

        # Create a list for downloaded post numbers.
        # We will later check if something from our database is missing in this list and remove it.
        # The reason for that is very simple: Storing files which got removed from 4chan on private server is not recommended.
        post_numbers = []

        # Add posts.
        for post_json in thread_json['posts']:
            # Create container class and parse info in the process.
            post_data = PostData(post_json)
            
            post_numbers.append(post_data.number)
            
            if post_data.number > last_post_number:
                try:
                    # Download images first, don't waste time when in transaction.
                    if not post_data.filename is None:
                        try:
                            image_tmp = ContentFile(self.get_image(post_data.filename, post_data.extension))
                            thumbnail_tmp = ContentFile(self.get_thumbnail(post_data.filename))

                            filename_image = format('%s%s' % (post_data.filename, post_data.extension))
                            filename_thumbnail = format('%s%s' % (post_data.filename, '.jpg'))

                        except:
                            raise ScrapError('Unable to download an image. Stopping at this post.')

                    # Save post in the database.
                    with transaction.atomic():
                        # Save post.
                        post = Post(
                            thread=thread,
                            number=post_data.number,
                            time=post_data.time,
                            name=post_data.name,
                            trip=post_data.trip,
                            email=post_data.email,
                            subject=post_data.subject,
                            comment=post_data.comment
                        )
                        post.save()

                        # Save image.
                        if not post_data.filename is None:
                            image = Image(original_name=post_data.original_filename, post=post)

                            image.image.save(filename_image, image_tmp)
                            image.thumbnail.save(filename_thumbnail, thumbnail_tmp)

                            image.save()
                        else:
                            image = None

                        self.triggers.handle(post_data, thread)

                    self.added_posts += 1
  

                except Exception as e:
                    raise

                # Just to give something to look at. 
                # "_" is a post withour an image, "-" is a post with an image
                if self.show_progress:
                    if post_data.filename is None:
                        character = '_'
                    else:
                        character = '-'
                    print(character, end="", flush=True)
    
        # Remove posts which does not exist in the thead.
        for post in thread.post_set.all():
            if not post.number in post_numbers:
                post.delete()
                self.removed_posts += 1


    def update(self):
        """Call this to update the database."""

        catalog = self.get_catalog_json()

        for page in catalog:
            for thread in page['threads']:
                # Download/update thread.
                try:
                    # Just info.
                    self.processed_threads += 1
                    if self.show_progress:
                        print('[%s]' % self.processed_threads, end="", flush=True)

                    stats = self.handle_thread(thread)

                    if self.show_progress:
                        print('', flush=True)

                except Exception as e:
                    sys.stderr.write('%s\n' % (e))
