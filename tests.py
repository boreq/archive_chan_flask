import datetime
import json
import os
import tempfile
import unittest
from flask import url_for
import archive_chan
from archive_chan.database import db
from archive_chan.lib.helpers import utc_now


def add_model(model, **kwargs):
    item = model(**kwargs)
    db.session.add(item)
    db.session.commit()
    db.session.refresh(item)
    return item

    
def add_board(**kwargs):
    return add_model(archive_chan.models.Board, **kwargs)


def add_thread(**kwargs):
    return add_model(archive_chan.models.Thread, **kwargs)


def add_post(**kwargs):
    return add_model(archive_chan.models.Post, **kwargs)


def add_update(**kwargs):
    return add_model(archive_chan.models.Update, **kwargs)


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + self.db_path,
        }
        self.app = archive_chan.create_app(config)
        self.client = self.app.test_client()
        archive_chan.database.init_db()
        self.set_up()

    def set_up(self):
        """Custom set up here."""
        pass

    def tearDown(self):
        self.tear_down()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def tear_down(self):
        """Custom tear down here."""
        pass

    def url_for(self, name, **kwargs):
        with self.app.test_request_context():
            return url_for(name, **kwargs)


class SimpleFilterTest(BaseTestCase):
    def set_up(self):
        self.parameters = (
            ('default', ('Default', None)),
            ('option', ('Option', {'field': True})),
        )

    def test_none(self):
        modifier = archive_chan.lib.modifiers.SimpleFilter(
            self.parameters,
            None
        )
        self.assertEqual(modifier.get(), 'default')

    def test_default(self):
        modifier = archive_chan.lib.modifiers.SimpleFilter(
            self.parameters,
            'default'
        )
        self.assertEqual(modifier.get(), 'default')

    def test_option(self):
        modifier = archive_chan.lib.modifiers.SimpleFilter(
            self.parameters,
            'option'
        )
        self.assertEqual(modifier.get(), 'option')

    def test_wrong(self):
        modifier = archive_chan.lib.modifiers.SimpleFilter(
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
        modifier = archive_chan.lib.modifiers.SimpleSort(
            self.parameters,
            None
        )
        self.assertEqual(modifier.get(), ('default', True))

    def test_default(self):
        modifier = archive_chan.lib.modifiers.SimpleSort(
            self.parameters,
            'default'
        )
        self.assertEqual(modifier.get(), ('default', False))

    def test_option(self):
        modifier = archive_chan.lib.modifiers.SimpleSort(
            self.parameters,
            'option'
        )
        self.assertEqual(modifier.get(), ('option', False))

    def test_option_reverse(self):
        modifier = archive_chan.lib.modifiers.SimpleSort(
            self.parameters,
            '-option'
        )
        self.assertEqual(modifier.get(), ('option', True))

    def test_wrong(self):
        modifier = archive_chan.lib.modifiers.SimpleSort(
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
        board = add_board(name='board')
        params = {'board': board.name}
        views.extend([
            ('board', params),
            ('board_stats', params),
            ('board_gallery', params),
        ])
        self.check_list('core', views)

        # Board and empty thread.
        thread = add_thread(board=board, number=1, first_reply=utc_now(), last_reply=utc_now())
        params = {'board': board.name, 'thread': thread.number}
        views.extend([
            ('thread', params),
            ('thread_stats', params),
            ('thread_gallery', params),
        ])
        self.check_list('core', views)

    def test_api_status(self):
        url = self.url_for('api.status')
        board1 = add_board(name='board1')
        board2 = add_board(name='board2')

        # Check for empty db table.
        response, response_data  = self.get_json(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('last_updates' in response_data, True)
        self.assertEqual(len(response_data['last_updates']) == 0, True)
        self.assertEqual('chart_data' in response_data, True)
        self.assertEqual(len(response_data['chart_data']['rows']) == 0, True)

        # Check for one ongoing update.
        update1 = add_update(board=board1, start=utc_now(), end=utc_now(),
                             status=archive_chan.models.Update.CURRENT,
                             used_threads=1)

        response, response_data = self.get_json(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('last_updates' in response_data, True)
        self.assertEqual(len(response_data['last_updates']) == 1, True)
        self.assertEqual('chart_data' in response_data, True)
        self.assertEqual(len(response_data['chart_data']['rows']) == 0, True)

        # Check for multiple different updates.
        update2 = add_update(board=board1, start=utc_now(), end=utc_now(),
                             status=archive_chan.models.Update.COMPLETED,
                             used_threads=1)
        update3 = add_update(board=board2, start=utc_now(), end=utc_now(),
                             status=archive_chan.models.Update.FAILED,
                             used_threads=1)

        response, response_data = self.get_json(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual('last_updates' in response_data, True)
        self.assertEqual(len(response_data['last_updates']) == 2, True)
        self.assertEqual('chart_data' in response_data, True)
        self.assertEqual(len(response_data['chart_data']['rows']) == 1, True)


if __name__ == '__main__':
    unittest.main()
