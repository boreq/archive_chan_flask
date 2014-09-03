import datetime
import json
import os
import tempfile
import time
import unittest
from flask import url_for
from flask.ext.login import current_user
from archive_chan import create_app, models, database, auth, cache
from archive_chan.lib import scraper, modifiers, helpers
from archive_chan.lib.helpers import utc_now, timestamp_to_datetime


_sample_thread_json = json.loads("""
{
    "no":43711727,
    "now":"08/21/14(Thu)15:54:54",
    "name":"Anonymous",
    "com":"So /g/, Google or Bing?",
    "filename":"Bing_vs_Google",
    "ext":".jpg",
    "w":640,
    "h":480,
    "tn_w":250,
    "tn_h":187,
    "tim":1408650894195,
    "time":1408650894,
    "md5":"CpKcHHPE64XPfGl5Mo0fyg==",
    "fsize":22710,
    "resto":0,
    "bumplimit":0,
    "imagelimit":0,
    "semantic_url":"so-g-google-or-bing",
    "replies":17,
    "images":2,
    "omitted_posts":12,
    "omitted_images":2,
    "last_replies":[{
        "no":43712273,
        "now":"08/21/14(Thu)16:25:19",
        "name":"Anonymous",
        "com":"Comment.",
        "filename":"your waifu is a slut",
        "ext":".gif",
        "w":530,
        "h":397,
        "tn_w":125,
        "tn_h":93,
        "tim":1408652719504,
        "time":1408652719,
        "md5":"MDTOYF2ufUDffz5M8+Qvhw==",
        "fsize":2724240,
        "resto":43711727
    }]
}
""")

_sample_post_json = json.loads("""
{
    "no":43722387,
    "now":"08/22/14(Fri)04:22:23",
    "name":"Anonymous",
    "com":"Comment.",
    "country":"TR",
    "filename":"1408694335049",
    "trip":"!Mysonoot.M",
    "sub":"Subject.",
    "ext":".png",
    "w":616,
    "h":294,
    "tn_w":125,
    "tn_h":59,
    "tim":1408695743383,
    "time":1408695743,
    "md5":"zB7h9/tETw1UON1PXEyefQ==",
    "fsize":53382,
    "resto":43722299
}
""")

_sample_post_json_minimal = json.loads("""
{
    "no":43722387,
    "time":1408695743
}
""")


class BaseTestCase(unittest.TestCase):

    def get_config(self, db_path):
        config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + db_path,
        }
        return config

    def setUp(self):
        # Database tmp file.
        self.db_fd, self.db_path = tempfile.mkstemp()
        # App and test client.
        config = self.get_config(self.db_path)
        self.app = create_app(config=config, envvar=None)
        self.client = self.app.test_client()
        # App context.
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        # Init database.
        database.init_db()
        # Request context.
        self.request_ctx = self.app.test_request_context()
        self.request_ctx.push()
        self.setup()

    def tearDown(self):
        self.teardown()
        self.request_ctx.pop()
        self.app_ctx.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def setup(self):
        """Custom setup here."""
        pass

    def teardown(self):
        """Custom teardown here."""
        pass

    def add_model(self, model, **kwargs):
        item = model(**kwargs)
        database.db.session.add(item)
        database.db.session.commit()
        database.db.session.refresh(item)
        return item

    @property
    def sample_thread_json(self):
        return _sample_thread_json.copy()

    @property
    def sample_post_json(self):
        return _sample_post_json.copy()

    @property
    def sample_post_json_minimal(self):
        return _sample_post_json_minimal.copy()

    def assertRises(self, exception, callable, *args, **kwargs):
        try:
            callable(*args, **kwargs)
        except exception as e:
            return
        except Exception as e:
            self.fail('%s was risen instead of %s' % (repr(e), exception))
        self.fail('%s was not risen' % exception)


class SimpleFilterTest(BaseTestCase):

    def setup(self):
        self.parameters = (
            ('default', ('Default', None)),
            ('option', ('Option', (models.Thread.saved==True,))),
        )

    def get_modifier(self, parameter):
        return modifiers.SimpleFilter(self.parameters, parameter)

    def test_parameter(self):
        modifier = self.get_modifier(None)
        self.assertEqual(modifier.get(), 'default')

        modifier = self.get_modifier('default')
        self.assertEqual(modifier.get(), 'default')

        modifier = self.get_modifier('option')
        self.assertEqual(modifier.get(), 'option')

        modifier = self.get_modifier('wrong_value')
        self.assertEqual(modifier.get(), 'default')

    def test_execute(self):
        board = self.add_model(models.Board, name='g')
        self.add_model(models.Thread, number=1, board=board, saved=True)
        self.add_model(models.Thread, number=2, board=board, saved=False)

        modifier = self.get_modifier('option')
        query1 = models.Thread.query
        query2 = modifier.execute(query1)
        self.assertEqual(len(query1.all()), 2)
        self.assertEqual(len(query2.all()), 1)


class SimpleSortTest(BaseTestCase):

    def setup(self):
        self.parameters = (
            ('default', ('Last reply', 'field', None)),
            ('option', ('Creation date', 'other_field', None)),
        )

    def get_modifier(self, parameter):
        return modifiers.SimpleSort(self.parameters, parameter)

    def test_parameter(self):
        modifier = self.get_modifier(None)
        self.assertEqual(modifier.get(), ('default', True))

        modifier = self.get_modifier('default')
        self.assertEqual(modifier.get(), ('default', False))

        modifier = self.get_modifier('option')
        self.assertEqual(modifier.get(), ('option', False))

        modifier = self.get_modifier('-option')
        self.assertEqual(modifier.get(), ('option', True))

        modifier = self.get_modifier('wrong_value')
        self.assertEqual(modifier.get(), ('default', True))


class ViewsTest(BaseTestCase):

    def check_list(self, blueprint_name, view_list):
        for view in view_list:
            url = url_for('%s.%s' % (blueprint_name, view[0]), **view[1])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def get_json(self, url, method='GET'):
        response = self.client.get(url, method=method)
        response_data = json.loads(response.data.decode())
        return (response, response_data)

    def test_core(self):
        """Check if core views return status code 200."""

        views = [
            ('index', {}),
            ('stats', {}),
            ('gallery', {}),
            ('status', {}),
        ]

        # Empty.
        self.check_list('core', views)

        # Board only.
        board = self.add_model(models.Board, name='board')
        params = {'board': board.name}
        views.extend([
            ('board', params),
            ('board_stats', params),
            ('board_gallery', params),
        ])
        self.check_list('core', views)

        # Board and empty thread.
        thread = self.add_model(models.Thread, board=board, number=1,
                           first_reply=utc_now(), last_reply=utc_now())
        params = {'board': board.name, 'thread': thread.number}
        views.extend([
            ('thread', params),
            ('thread_stats', params),
            ('thread_gallery', params),
        ])
        self.check_list('core', views)


class ThreadScraperTest(BaseTestCase):

    def setup(self):
        self.thread_data = scraper.ThreadData(self.sample_thread_json)
        self.thread_scraper = scraper.ThreadScraper(None, self.thread_data)
        self.thread = models.Thread(last_reply=self.thread_data.last_reply_time,
                                    replies=self.thread_data.replies + 1)

    def test_should_update_same(self):
        self.assertFalse(self.thread_scraper.should_be_updated(self.thread))

    def test_should_update_less_replies(self):
        self.thread.replies -= 1
        self.assertTrue(self.thread_scraper.should_be_updated(self.thread))

    def test_should_update_older(self):
        self.thread.last_reply -= datetime.timedelta(minutes=2)
        self.assertTrue(self.thread_scraper.should_be_updated(self.thread))

    def test_should_update_broken(self):
        broken_thread = models.Thread(last_reply=None, replies=0)
        self.assertTrue(self.thread_scraper.should_be_updated(broken_thread))


class ThreadDataTest(BaseTestCase):

    def test_basics(self):
        """Test if all properties are populated correctly."""
        thread_data = scraper.ThreadData(self.sample_thread_json)
        # number
        self.assertEqual(thread_data.number, self.sample_thread_json['no'])
        self.assertEqual(type(thread_data.number), int)
        # replies
        self.assertEqual(thread_data.replies, self.sample_thread_json['replies'])
        self.assertEqual(type(thread_data.replies), int)
        # last_reply_time
        last_reply_time = self.sample_thread_json['last_replies'][-1]['time']
        last_reply_time = timestamp_to_datetime(last_reply_time)
        self.assertEqual(thread_data.last_reply_time, last_reply_time)
        self.assertEqual(type(thread_data.last_reply_time), datetime.datetime)

    def test_last_reply_time_gone(self):
        """Test that there is no exception if the last_replies list doesn't
        exist.
        """
        thread_json = self.sample_thread_json
        thread_json.pop('last_replies')
        thread_data = scraper.ThreadData(thread_json)

    def test_last_reply_time_empty(self):
        """Test that there is no exception if the last_replies list is empty."""
        thread_json = self.sample_thread_json
        thread_json['last_replies'] = []
        thread_data = scraper.ThreadData(thread_json)


class PostDataTest(BaseTestCase):

    def test_basics(self):
        """Test if all properties are populated correctly."""
        post_data = scraper.PostData(self.sample_post_json)

        # Correct copy.
        properties = (
            ('no', 'number', int, lambda x: x),
            ('time', 'time', datetime.datetime, lambda x: timestamp_to_datetime(x)),
            ('name', 'name', str, lambda x: x),
            ('trip', 'trip', str, lambda x: x),
            ('country', 'country', str, lambda x: x),
            ('name', 'name', str, lambda x: x),
            ('sub', 'subject', str, lambda x: x),
            ('com', 'comment', str, lambda x: x),
            ('tim', 'filename', str, lambda x: str(x)),
            ('ext', 'extension', str, lambda x: x),
            ('filename', 'original_filename', str, lambda x: x),
        )

        for entry in properties:
            self.assertEqual(getattr(post_data, entry[1]),
                             entry[3](self.sample_post_json[entry[0]]),
                             msg='%s: does not match' % entry[1])

            self.assertEqual(type(getattr(post_data, entry[1])),
                             entry[2],
                             msg='%s: wrong type' % entry[1])

    def test_defaults(self):
        """Test if all properties default to corect values."""
        post_data = scraper.PostData(self.sample_post_json_minimal)

        properties = (
            ('name', ''),
            ('trip', ''),
            ('country', ''),
            ('name', ''),
            ('subject', ''),
            ('comment', ''),
            ('filename', None),
            ('extension', None),
            ('original_filename', None),
        )

        for entry in properties:
            self.assertEqual(getattr(post_data, entry[0]),
                             entry[1],
                             msg='%s: wrong default' % entry[0])


class TriggersTest(BaseTestCase):

    def test_check_post_type(self):
        """Test if post type is checked correctly."""
        board = self.add_model(models.Board, name='board')
        thread = self.add_model(models.Thread, board=board, number=1)

        triggers = scraper.Triggers()
        post_data = scraper.PostData(self.sample_post_json)

        post_data.number = 1
        trigger = models.Trigger(post_type='master')
        self.assertTrue(triggers.check_post_type(trigger, thread, post_data))

        post_data.number = 2
        trigger = models.Trigger(post_type='master')
        self.assertFalse(triggers.check_post_type(trigger, thread, post_data))

        post_data.number = 1
        trigger = models.Trigger(post_type='sub')
        self.assertFalse(triggers.check_post_type(trigger, thread, post_data))

        post_data.number = 2
        trigger = models.Trigger(post_type='master')
        self.assertFalse(triggers.check_post_type(trigger, thread, post_data))

    def test_check_event(self):
        """Test if the event is checked correctly."""
        def get_trigger(event):
            return models.Trigger(field='comment', event=event, phrase='phrase',
                                  case_sensitive=True)

        def check(trigger_true, trigger_false):
            self.assertTrue(triggers.check_event(trigger_true, post_data))
            self.assertFalse(triggers.check_event(trigger_false, post_data))

        triggers = scraper.Triggers()
        post_data = scraper.PostData(self.sample_post_json)

        # contains and containsno
        trigger = get_trigger('contains')
        trigger_no = get_trigger('containsno')
        post_data.comment = 'there is a phrase in this comment'
        check(trigger, trigger_no)
        post_data.comment = 'this one does not contain it'
        check(trigger_no, trigger)

        # is and isnot
        trigger = get_trigger('is')
        trigger_no = get_trigger('isnot')
        post_data.comment = 'phrase'
        check(trigger, trigger_no)
        post_data.comment = 'is not a phrase'
        check(trigger_no, trigger)

        # begins and ends
        trigger = get_trigger('begins')
        trigger_no = get_trigger('ends')
        post_data.comment = 'phrase starts it'
        check(trigger, trigger_no)
        post_data.comment = 'ends with phrase'
        check(trigger_no, trigger)

    def test_handle(self):
        """Test if the trigger saves the thread and adds the tag."""
        post_data = scraper.PostData(self.sample_post_json)

        board = self.add_model(models.Board, name='board')
        thread = self.add_model(models.Thread, board=board, number=1)
        tag = self.add_model(models.Tag, name='tag')
        trigger = self.add_model(models.Trigger, field='comment', event='is',
                                 post_type='any', phrase=post_data.comment,
                                 case_sensitive=True, tag=tag, save_thread=True)

        triggers = scraper.Triggers()
        triggers.handle(post_data, thread)
        database.db.session.commit()

        self.assertEqual(len(models.TagToThread.query.all()), 1,
                         msg='Trigger failed to add the tag.')
        self.assertTrue(models.Thread.query.first().saved,
                         msg='Trigger failed to save the thread.')
        self.assertTrue(models.TagToThread.query.first().automatically_added,
                         msg='Tag was not marked as automatically added.')


class CacheTestMixin(object):
    """Contains general tests for all cache systems."""

    cache_class = None
    fail_message = 'Failed.'

    def setup(self):
        super(CacheTestMixin, self).setup()
        self.assertIsNotNone(self.cache_class, 'Set cache_class in this class.')
        self.cache = cache.cache

    def test_system(self):
        self.assertIsInstance(self.cache._client, self.cache_class)

    def test_key(self):
        key1 = cache.get_cache_key(False)
        key2 = cache.get_cache_key(True)
        self.assertNotEqual(key1, key2)

    def test_set_get(self):
        self.assertTrue(self.cache.set('key', 'value'), self.fail_message)
        self.assertEqual(self.cache.get('key'), 'value', self.fail_message)
    
    def test_wrapper_expire(self):
        now = cache.cached(timeout=1)(utc_now)
        value = now()
        time.sleep(2)
        self.assertNotEqual(now(), value)

    def test_wrapper(self):
        now = cache.cached(timeout=2)(utc_now)
        value = now()
        time.sleep(1)
        self.assertEqual(now(), value, self.fail_message)


class NoCacheTest(CacheTestMixin, BaseTestCase):
    """Caching should not occur."""

    from werkzeug.contrib.cache import NullCache
    cache_class = NullCache

    def test_set_get(self):
        self.assertRises(AssertionError,
                         super(NoCacheTest, self).test_set_get)

    def test_wrapper(self):
        self.assertRises(AssertionError,
                         super(NoCacheTest, self).test_wrapper)


class MemcachedCacheTest(CacheTestMixin, BaseTestCase):

    from werkzeug.contrib.cache import MemcachedCache
    cache_class = MemcachedCache
    fail_message = 'Is memcached daemon running?'

    def get_config(self, *args, **kwargs):
        config = BaseTestCase.get_config(self, *args, **kwargs)
        config['MEMCACHED_URL'] = ['127.0.0.1:11211']
        return config


class AuthTest(BaseTestCase):

    def setup(self):
        password = auth.generate_password_hash('pass')
        self.add_model(models.User, username='user',
                       password=password)
        self.assertFalse(current_user.is_authenticated())

    def test_logout_not_auth(self):
        """It should be possible to log out even when not logged in."""
        self.assertTrue(auth.logout())

    def test_login_failed(self):
        self.assertFalse(auth.login('wronguser', 'pass'))
        self.assertFalse(auth.login('user', 'wrongpass'))

    def test_login_logout(self):
        self.assertTrue(auth.login('user', 'pass'))
        self.assertTrue(current_user.is_authenticated())

        self.assertTrue(auth.logout())
        self.assertFalse(current_user.is_authenticated())

    def test_hashing(self):
        password = auth.generate_password_hash('pass')
        self.assertTrue(auth.check_password_hash(password, 'pass'))


class HelpersTest(BaseTestCase):

    def test_get_or_create(self):
        get_board = lambda: helpers.get_or_create(database.db.session, models.Board,
                                                  name='g')
        board, created = get_board()
        self.assertTrue(created)
        self.assertIsInstance(board, models.Board)

        board, created = get_board()
        self.assertFalse(created)
        self.assertIsInstance(board, models.Board)

    def test_utc_now(self):
        self.assertIsNotNone(helpers.utc_now().tzinfo)
    
    def test_timestamp_to_datetime(self):
        self.assertIsNotNone(helpers.timestamp_to_datetime(0).tzinfo)
    

if __name__ == '__main__':
    unittest.main()
