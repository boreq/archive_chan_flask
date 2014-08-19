import datetime
import html
import io
import re
import requests
import sys
import threading
import time
import pytz
from flask import current_app
from sqlalchemy.orm.attributes import instance_state
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.datastructures import FileStorage
from .. import create_app
from ..database import db
from ..models import Board, Thread, Post, Image, Trigger, TagToThread, Update, Tag


app = create_app()


class ScrapError(Exception):
    pass


class ThreadInfo:
    """Class used for storing information about the thread."""

    def __init__(self, thread_json): 
        self.number = thread_json['no']
        
        # Get the time of the last reply or thread creation time.
        if 'last_replies' in thread_json and len(thread_json) > 0:
            last_reply_time = int(thread_json['last_replies'][-1]['time'])
        else:
            last_reply_time = int(thread_json['time'])

        # Add timezone information to the datetime.
        self.last_reply_time = pytz.utc.localize(
            datetime.datetime.fromtimestamp(last_reply_time)
        )

        # 4chan doesn't count the first post.
        self.replies = int(thread_json['replies'])


class PostData:
    """Class used for storing information about the post."""

    def replace_content(self, text):
        """Cleans the HTML from the post comment. Returns a string."""
        # Remove >>quotes.
        text = re.sub(r'\<a.*?class="quotelink".*?\>(.*?)\</a\>', r'\1', text)

        # Remove spans: >le meme arrows/deadlinks etc.
        text = re.sub(r'\<span.*?\>(.*?)\</span\>', r'\1', text)

        # Replace <pre> with [code].
        text = re.sub(r'\<pre.*?\>(.*?)\</pre\>', r'[code]\1[/code]', text)

        # Replace <br> with newline character.
        text = text.replace('<br>', '\n')

        # Remove <wbr>.
        text = text.replace('<wbr>', '')

        # Unescape characters.
        text = html.unescape(text)

        return text

    def __init__(self, post_json): 
        """Loads the data from JSON retrieved from the thread API."""
        self.number = int(post_json['no'])
        self.time = pytz.utc.localize(
            datetime.datetime.fromtimestamp(int(post_json['time']))
        )

        self.name = post_json.get('name', '')
        self.trip = post_json.get('trip', '')
        self.email = post_json.get('email', '')
        self.country = post_json.get('country', '')

        self.subject = self.replace_content(post_json.get('sub', ''))
        self.comment = self.replace_content(post_json.get('com', ''))

        self.filename = post_json.get('tim')
        self.extension = post_json.get('ext')
        self.original_filename = post_json.get('filename')


class Triggers:
    """Class handling triggers."""

    def __init__(self):
        # Prepare trigger list.
        self.triggers = Trigger.query.outerjoin(Tag).filter(Trigger.active==True).all()

    def check_post_type(self, trigger, thread, post_data):
        """True if the type of the post (master - first post, sub - reply)
        is correct, false otherwise.
        """
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
            return field_value.endswith(trigger_value)

        return False

    def get_single_trigger_actions(self, trigger, thread, post_data):
        """Returns a set of actions to execute based on one trigger."""
        if not self.check_post_type(trigger, thread, post_data):
            return None
        
        actions = set()

        if self.check_event(trigger, post_data):
            if trigger.save_thread:
                actions.add(('save', 0))
            if trigger.tag is not None:
                actions.add(('add_tag', trigger.tag))

        return actions

    def get_actions(self, thread, post_data):
        """Returns a set of actions to execute."""
        actions = set()

        # Prepare a set of actions to execute.
        for trigger in self.triggers:
            new_actions = self.get_single_trigger_actions(trigger, thread,
                                                          post_data)
            if not new_actions is None:
                actions = actions | new_actions
        return actions

    def handle(self, post_data, thread):
        """Main function called to execute the triggers."""
        actions = self.get_actions(thread, post_data)

        # Execute actions.
        for action in actions:
            if action[0] == 'save' and not thread.saved:
                thread.saved = True
                thread.auto_saved = True
                db.session.add(thread)

            if action[0] == 'add_tag':
                if TagToThread.query.filter(
                        TagToThread.thread==thread,
                        TagToThread.tag==action[1]
                    ).first() is None:
                    tag_to_thread = TagToThread(
                        thread_id=thread.id,
                        tag_id=action[1].id,
                        automatically_added=True
                    )
                    if instance_state(tag_to_thread).transient:
                        db.session.add(tag_to_thread)


class Queuer:
    """Exposes the functions which allow the threads to synchronise their wait
    times to prevent accessing the API too often.
    """

    def __init__(self):
        self.last_api_request = None
        self.last_file_request = None

        self.total_wait = 0
        self.total_wait_time_with_lock = datetime.timedelta()

        self.file_wait_lock = threading.Lock()
        self.api_wait_lock = threading.Lock()

    def get_total_wait_time(self):
        """Get the total time for which this class forced the threads to wait.
        This is used for generating statistics.
        """
        return datetime.timedelta(seconds=self.total_wait)

    def get_total_wait_time_with_lock(self):
        """Get the total time for which this class forced the threads to wait
        plus the time spent waiting for the lock. This is used for generating
        statistics.
        """
        return self.total_wait_time_with_lock

    def wait(self, time_beetwen_requests, last_request):
        """Wait to make sure that the specified time passed since the last
        request.
        """
        # Convert seconds to microseconds.
        time_beetwen_requests *= 1000000
        if not last_request is None:
            time_passed = datetime.datetime.now() - last_request
            if time_passed.microseconds < time_beetwen_requests:
                wait_for_seconds = (time_beetwen_requests - \
                                    time_passed.microseconds) / 1000000
                self.total_wait += wait_for_seconds
                time.sleep(wait_for_seconds)

    def api_wait(self):
        """Wait in order to satisfy the API rules. Called before each API
        query.
        """
        wait_start = datetime.datetime.now()
        with self.api_wait_lock:
            self.wait(current_app.config.get('API_WAIT'), self.last_api_request)
            self.last_api_request = datetime.datetime.now()
        self.total_wait_time_with_lock += datetime.datetime.now() - wait_start

    def file_wait(self):
        """Wait in order to satisfy the rules. Called before each file
        download.
        """
        wait_start = datetime.datetime.now()
        with self.file_wait_lock:
            self.wait(current_app.config.get('FILE_WAIT'), self.last_file_request)
            self.last_file_request = datetime.datetime.now()
        self.total_wait_time_with_lock += datetime.datetime.now() - wait_start


class Stats:
    """Class storing the statistics. Perfomed tasks are purely informational
    are not not a part of any other mechanic.
    """

    def __init__(self):
        self.parameters = {
            'total_download_time': datetime.timedelta(),
            'total_wait_time': datetime.timedelta(),
            'total_wait_time_with_lock': datetime.timedelta(),
            'processed_threads':  0,
            'added_posts': 0,
            'removed_posts': 0,
            'downloaded_images': 0,
            'downloaded_thumbnails': 0,
            'downloaded_threads': 0,
        }
        
        self.lock = threading.Lock()

    def add(self, name, value):
        """Add a value to the specified statistic."""
        with self.lock:
            self.parameters[name] += value

    def get(self, name):
        """Get a value of the specified statistic."""
        with self.lock:
            return self.parameters[name]

    def add_to_record(self, record, total_time, **kwargs):
        """Save the statistics in the database."""
        used_threads = kwargs.get('used_threads',
                                  current_app.config.get('SCRAPER_THREADS_NUMBER'))
        wait_time = self.get('total_wait_time_with_lock') \
                        .total_seconds() / used_threads
        download_time = self.get('total_download_time') \
                            .total_seconds() / used_threads
        record.total_time = total_time.total_seconds()
        record.wait_time = wait_time
        record.download_time = download_time
        record.processed_threads = self.get('processed_threads')
        record.added_posts = self.get('added_posts')
        record.removed_posts = self.get('removed_posts')
        record.downloaded_images = self.get('downloaded_images')
        record.downloaded_thumbnails = self.get('downloaded_thumbnails')
        record.downloaded_threads = self.get('downloaded_threads')
        return record

    def get_text(self, total_time, **kwargs):
        """Get the text for printing. Total processing time must be provided
        externally.
        """
        try:
            wait_percent = round(
                self.get('total_wait_time_with_lock').total_seconds() \
                / total_time.total_seconds() * 100 \
                / current_app.config.get('SCRAPER_THREADS_NUMBER')
            )
            downloading_percent = round(
                self.get('total_download_time').total_seconds() \
                / total_time.total_seconds() * 100 \
                / current_app.config.get('SCRAPER_THREADS_NUMBER')
            )

        except:
            # Division by zero. Set to 0 for the statistics.
            wait_percent = 0
            downloading_percent = 0

        return 'Time passed: %s seconds (%s%% waiting, %s%% downloading files) Processed threads: %s Added posts: %s Removed posts: %s Downloaded images: %s Downloaded thumbnails: %s Downloaded threads: %s' % (
            round(total_time.total_seconds(), 2),
            wait_percent,
            downloading_percent,
            self.get('processed_threads'),
            self.get('added_posts'),
            self.get('removed_posts'),
            self.get('downloaded_images'),
            self.get('downloaded_thumbnails'),
            self.get('downloaded_threads'),
        )

    def merge(self, stats):
        """Merge the data from other instance of this class."""
        for key in self.parameters:
            self.add(key, stats.get(key))


class Scraper(object):
    """Base class for the scrapers."""

    def __init__(self, board, **kwargs):
        """Board is a database object, not a board name.
        Accepted kwargs: bool progress, Queuer queuer
        """
        self.board = board
        self.stats = Stats()
        self.queuer = kwargs.get('queuer', Queuer())
        self.show_progress = kwargs.get('progress', False)
        
    def get_url(self, url):
        """Download data from an url."""
        download_start = datetime.datetime.now()
        data = requests.get(url, timeout=current_app.config.get('CONNECTION_TIMEOUT'))
        self.stats.add('total_download_time',
                        datetime.datetime.now() - download_start)
        return data


class ThreadScraper(Scraper):
    """Scraps the data from a single thread."""

    def __init__(self, board, thread_info, **kwargs):
        """Accepted kwargs: Triggers triggers + base class kwargs"""
        super(ThreadScraper, self).__init__(board, **kwargs)
        self.thread_info = thread_info
        self.triggers = Triggers()
        self.modified = False

    def get_image(self, filename, extension):
        """Download an image."""
        url = 'https://i.4cdn.org/%s/%s%s' % (
            self.board.name,
            filename,
            extension
        )
        self.queuer.file_wait()
        self.stats.add('downloaded_images', 1)
        return self.get_url(url).content

    def get_thumbnail(self, filename):
        """Download a thumbnail."""
        url = 'https://t.4cdn.org/%s/%ss.jpg' % (self.board.name, filename)
        self.queuer.file_wait()
        self.stats.add('downloaded_thumbnails', 1)
        return self.get_url(url).content

    def get_thread_json(self, thread_number):
        """Get the thread data from the official API."""
        url = 'https://a.4cdn.org/%s/thread/%s.json' % (
            self.board.name,
            thread_number
        )
        self.queuer.api_wait()
        self.stats.add('downloaded_threads', 1)
        return self.get_url(url).json()
    
    def get_thread_number(self):
        """Get the number of a thread scrapped by this instance."""
        return self.thread_info.number

    def should_be_updated(self, thread):
        """Determine if the thread should be updated."""
        # Should the thread be updated? Check only if there is any data about
        # the thread (the download of the first post was successful)
        if not thread.last_reply_time() is None and thread.posts.count() > 0:
            # It has to have newer replies or different number of replies.
            # Note: use count_replies because 4chan does not count the first
            # post as a reply.
            if (self.thread_info.last_reply_time <= thread.last_reply_time()
                and self.thread_info.replies == thread.count_replies()):
                return False

        return True

    def get_last_post_number(self, thread):
        """Determine the last post's number or pick an imaginary one.
        Only posts with a number above this one will be added to the database.
        """
        last_post = thread.posts.order_by(Post.number.desc()).first()
        if last_post is not None:
            return last_post.number
        return -1

    def add_post(self, post_data, thread):
        """Add the post to the database."""
        # Download the images.
        if not post_data.filename is None:
            try:
                image_storage = FileStorage(
                    io.BytesIO(self.get_image(post_data.filename,
                                              post_data.extension))
                )
                thumbnail_storage = FileStorage(
                    io.BytesIO(self.get_thumbnail(post_data.filename))
                )
                filename_image = '%s%s' % (post_data.filename, post_data.extension)
                filename_thumbnail = '%s%s' % (post_data.filename, '.jpg')

            except:
                raise ScrapError('Image download failed. Stopping at this post.')

        # Save post.
        post = Post(
            thread=thread,
            number=post_data.number,
            time=post_data.time,
            name=post_data.name,
            trip=post_data.trip,
            email=post_data.email,
            country=post_data.country,
            subject=post_data.subject,
            comment=post_data.comment
        )
        if instance_state(post).transient:
            db.session.add(post)

        # Save image.
        if not post_data.filename is None:
            image = Image(original_name=post_data.original_filename, post=post)
            image.save_image(image_storage, filename_image)
            image.save_thumbnail(thumbnail_storage, filename_thumbnail)
            if instance_state(image).transient:
                db.session.add(image)

        # Just to give something to look at. 
        # "_" is a post without an image, "-" is a post with an image
        if self.show_progress:
            print('-' if post_data.filename else '_', end='', flush=True)
        self.stats.add('added_posts', 1)

    def delete_post(self, post):
        # SQL Alchemy's ORM events can not modify related objects and it is not
        # possible to create a single trigger for all supported databases.
        post.thread.post_deleted()
        if post.image is not None:
            post.thread.image_deleted()
        db.session.add(post.thread)

        db.session.delete(post)
        self.stats.add('removed_posts', 1)

    def handle_thread(self):
        """Download/update the thread if necessary."""
        # Download only above a certain number of posts.
        # (seriously it is wise do let the moderators do their job first)
        if self.thread_info.replies < self.board.replies_threshold:
            return

        # Get the existing entry for this thread from the database or create
        # a new record for it.
        try:
            thread = Thread.query.join(Board).filter(
                Board.name==self.board.name,
                Thread.number==self.thread_info.number
            ).one()
            if not self.should_be_updated(thread):
                return

        except NoResultFound:
            thread = Thread(board_id=self.board.name, number=self.thread_info.number)

        if not thread.id:
            db.session.add(thread)
            db.session.flush()
            db.session.refresh(thread)

        last_post_number = self.get_last_post_number(thread)

        # Download the thread data.
        try:
            thread_json = self.get_thread_json(self.thread_info.number)
        except:
            raise ScrapError('Unable to download the thread data. It might not exist anymore.')

        # Create a list of downloaded post numbers. Items present in
        # the database but missing here will be removed.
        post_numbers = []

        try:
            # Add posts.
            for post_json in thread_json['posts']:
                post_data = PostData(post_json)
                post_numbers.append(post_data.number)
                if post_data.number > last_post_number:
                    self.modified = True
                    self.add_post(post_data, thread)
                    self.triggers.handle(post_data, thread)
                    db.session.commit()

            # Remove posts which don't exist in the thread.
            for post in thread.posts.all():
                if not post.number in post_numbers:
                    self.modified = True
                    self.delete_post(post)
                    db.session.commit()

        except Exception as e:
            db.session.rollback()
            sys.stderr.write('%s\n' % e)
            self.modified = True


class ThreadScraperThread(ThreadScraper, threading.Thread):
    """This is simply a ThreadScraper which is supposed to run as a thread."""

    def __init__(self, board, thread_info, board_scraper, **kwargs):
        super().__init__(board, thread_info, **kwargs)
        threading.Thread.__init__(self)
        self.board_scraper = board_scraper

    def on_task_start(self):
        db.session()

    def on_task_end(self):
        db.session.remove()
        self.board_scraper.on_thread_scraper_done(self)

    def run(self):
        try:
            with app.test_request_context():
                self.on_task_start()
                self.handle_thread()

        except Exception as e:
            sys.stderr.write('%s\n' % e)

        finally:
            self.on_task_end()


class BoardScraper(Scraper):
    """Class which launches and coordinates ThreadScraperThread classes."""

    def __init__(self, board, **kwargs):
        super(BoardScraper, self).__init__(board, **kwargs)

        self.triggers = Triggers()

        self.thread_gen = None
        self.running_threads = []
        self.running_threads_lock = threading.Lock()

    def get_catalog_json(self):
        """Get the catalog data from the official API."""
        url = 'https://a.4cdn.org/%s/catalog.json' % (self.board.name)
        self.queuer.api_wait()
        return self.get_url(url).json()

    def on_thread_scraper_done(self, thread_scraper):
        """Called by a child thread after it finishes working."""
        try:
            # Merge the stats from the child thread.
            self.stats.merge(thread_scraper.stats)
        
        except Exception as e:
            sys.stderr.write('%s\n' % e)

        finally:
            # Launch a new thread in place of the one that just finished.
            self.launch_thread()

            # Remove the thread from the list of running threads.
            self.remove_running(thread_scraper.get_thread_number())

    def add_running(self, thread_number):
        """Add a thread to the list of the running threads."""
        with self.running_threads_lock:
            self.running_threads.append(thread_number)

    def remove_running(self, thread_number):
        """Remove a thread from the list of running threads."""
        with self.running_threads_lock:
            if thread_number in self.running_threads:
                self.running_threads.remove(thread_number)

    def launch_thread(self):
        """Launch a new ThreadScraperThread."""
        self.stats.add('processed_threads', 1)

        # Get a new thread from the generator.
        thread_data = self.get_thread()
        if thread_data is None:
            return

        # Prepare thread info class based on returned JSON.
        thread_info = ThreadInfo(thread_data)

        # Add a new thread to the list of all running threads.
        self.add_running(thread_info.number)

        try:
            # Launch the thread.
            with app.test_request_context():
                thread_scraper = ThreadScraperThread(self.board, thread_info, self,
                    queuer=self.queuer,
                    triggers=self.triggers,
                    progress=self.show_progress
                )
                thread_scraper.daemon = True
                thread_scraper.start()

        except Exception as e:
            # Remove the thread from the list of all running threads.
            self.remove_running(thread_info.number)
            sys.stderr.write('%s\n' % e)

    def get_thread(self):
        """Get the next thread."""
        if self.thread_gen is None:
            self.thread_gen = self.thread_generator()

        try:
            return next(self.thread_gen)

        except StopIteration:
            return None

    def thread_generator(self):
        """Generator for the thread JSON."""
        for page in self.catalog:
            for thread in page['threads']:
                yield thread

    def update(self):
        """Call this to update the database."""
        # Get the catalog from the API.
        try:
            self.catalog = self.get_catalog_json()

        except:
            raise ScrapError('Unable to download or parse the catalog data. Board update stopped.')

        # Launch the initial threads. Next ones will be launched automatically.
        for i in range(0, current_app.config.get('SCRAPER_THREADS_NUMBER')):
            self.launch_thread()

        # Wait for all threads to finish.
        while True:
            time.sleep(1)
            with self.running_threads_lock:
                if not len(self.running_threads):
                    break

        self.stats.add('total_wait_time', self.queuer.get_total_wait_time())
        self.stats.add('total_wait_time_with_lock', self.queuer.get_total_wait_time_with_lock())
