import datetime
import json
import os
import tempfile
import unittest
from flask import url_for
from archive_chan import create_app, models, database
from archive_chan.lib import scraper, modifiers
from archive_chan.lib.helpers import utc_now


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
    "filename":"1408694335049",
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


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + self.db_path,
        }
        self.app = create_app(config)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        database.init_db()
        self.set_up()

    def tearDown(self):
        self.tear_down()
        self.ctx.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def set_up(self):
        """Custom setup here."""
        pass

    def tear_down(self):
        """Custom teardown here."""
        pass

    def url_for(self, name, **kwargs):
        with self.app.test_request_context():
            return url_for(name, **kwargs)

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


class SimpleFilterTest(BaseTestCase):
    def set_up(self):
        self.parameters = (
            ('default', ('Default', None)),
            ('option', ('Option', {'field': True})),
        )

    def test_none(self):
        modifier = modifiers.SimpleFilter(
            self.parameters,
            None
        )
        self.assertEqual(modifier.get(), 'default')

    def test_default(self):
        modifier = modifiers.SimpleFilter(
            self.parameters,
            'default'
        )
        self.assertEqual(modifier.get(), 'default')

    def test_option(self):
        modifier = modifiers.SimpleFilter(
            self.parameters,
            'option'
        )
        self.assertEqual(modifier.get(), 'option')

    def test_wrong(self):
        modifier = modifiers.SimpleFilter(
            self.parameters,
            'wrong_value'
        )
        self.assertEqual(modifier.get(), 'default')


class SimpleSortTest(BaseTestCase):
    def set_up(self):
        self.parameters = (
            ('default', ('Last reply', 'field', None)),
            ('option', ('Creation date', 'other_field', None)),
        )

    def test_none(self):
        modifier = modifiers.SimpleSort(
            self.parameters,
            None
        )
        self.assertEqual(modifier.get(), ('default', True))

    def test_default(self):
        modifier = modifiers.SimpleSort(
            self.parameters,
            'default'
        )
        self.assertEqual(modifier.get(), ('default', False))

    def test_option(self):
        modifier = modifiers.SimpleSort(
            self.parameters,
            'option'
        )
        self.assertEqual(modifier.get(), ('option', False))

    def test_option_reverse(self):
        modifier = modifiers.SimpleSort(
            self.parameters,
            '-option'
        )
        self.assertEqual(modifier.get(), ('option', True))

    def test_wrong(self):
        modifier = modifiers.SimpleSort(
            self.parameters,
            'wrong_value'
        )
        self.assertEqual(modifier.get(), ('default', True))


class ViewsTest(BaseTestCase):
    def check_list(self, blueprint_name, view_list):
        for view in view_list:
            url = self.url_for('%s.%s' % (blueprint_name, view[0]), **view[1])
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
    def set_up(self):
        self.thread_info = scraper.ThreadInfo(self.sample_thread_json)
        self.thread_scraper = scraper.ThreadScraper(None, self.thread_info)
        self.thread = models.Thread(last_reply=self.thread_info.last_reply_time,
                                    replies=self.thread_info.replies + 1)
        
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


class ThreadInfoTest(BaseTestCase):
    def test_last_reply_time_gone(self):
        thread_json = self.sample_thread_json
        thread_json.pop('last_replies')
        thread_info = scraper.ThreadInfo(thread_json)

    def test_last_reply_time_empty(self):
        thread_json = self.sample_thread_json
        thread_json['last_replies'] = []
        thread_info = scraper.ThreadInfo(thread_json)

    def test_check_post_type(self):
        board = self.add_model(models.Board, name='board')


class TriggersTest(BaseTestCase):
    def test_check_post_type(self):
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
        

if __name__ == '__main__':
    unittest.main()
