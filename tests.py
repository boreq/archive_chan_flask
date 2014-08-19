import datetime
import json
import os
import tempfile
import unittest
from flask import Config
import archive_chan


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + self.db_path
        }
        self.app = archive_chan.create_app(config).test_client()
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


'''
class SimpleSortTest(BaseTestCase):
    def setUp(self):
        self.parameters = (
            ('default', ('Last reply', 'field', None)),
            ('option', ('Creation date', 'other_field', {'annotate': 'field'})),
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
    def setUp(self):
        self.views = [
            ('index', ()),
            ('stats', ()),
            ('gallery', ()),
            ('search', ()),
            ('status', ()),
        ]

        self.client = Client()

    def test_views(self):
        """Check if views return status code 200. AJAX/API views are not tested here."""
        def test_list(view_list):
            for view in view_list:
                response = self.client.get(reverse('archive_chan:%s' % view[0], args=view[1]))
                self.assertEqual(response.status_code, 200)

        # Empty.
        test_list(self.views)

        board = models.Board.objects.create(name='a')

        self.views.extend([
            ('board', (board.name)),
            ('board_stats', (board.name)),
            ('board_gallery', (board.name)),
            ('board_search', (board.name)),
        ])

        # Board only.
        test_list(self.views)

        thread = models.Thread.objects.create(board=board, number=1, first_reply=now, last_reply=now)

        self.views.extend([
            ('thread', (board.name, thread.number)),
            ('thread_stats', (board.name, thread.number)),
            ('thread_gallery', (board.name, thread.number)),
            ('thread_search', (board.name, thread.number)),
        ])

        # Board and empty thread.
        test_list(self.views)

        post = models.Post.objects.create(thread=thread, number=1, time=now)

        # Board and thread with one post.
        test_list(self.views)


class ApiTest(BaseTestCase):
    def setUp(self):
        self.client = Client()

        self.board_a = models.Board.objects.create(name='a')
        self.board_b = models.Board.objects.create(name='b')

    def get_api(self, url):
        response = self.client.get(url)
        response_data = json.loads(response.content.decode())
        return (response, response_data)

    def test_status(self):
        # Check for empty db table.
        response, response_data = self.get_api(reverse('archive_chan:api_status'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual('last_updates' in response_data and len(response_data['last_updates']) == 0, True)
        self.assertEqual('chart_data' in response_data and len(response_data['chart_data']['rows']) == 0, True)

        # Check for one ongoing update.
        update1 = models.Update.objects.create(board=self.board_a, start=now, end=now, status=models.Update.CURRENT, used_threads = 1)

        response, response_data = self.get_api(reverse('archive_chan:api_status'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual('last_updates' in response_data and len(response_data['last_updates']) == 1, True)
        self.assertEqual('chart_data' in response_data and len(response_data['chart_data']['rows']) == 0, True)

        # Check for multiple different updates.
        update2 = models.Update.objects.create(board=self.board_a, start=now, end=now, status=models.Update.COMPLETED, used_threads = 1)
        update3 = models.Update.objects.create(board=self.board_b, start=now, end=now, status=models.Update.FAILED, used_threads = 1)

        response, response_data = self.get_api(reverse('archive_chan:api_status'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual('last_updates' in response_data and len(response_data['last_updates']) == 2, True)
        self.assertEqual('chart_data' in response_data and len(response_data['chart_data']['rows']) == 1, True)

'''

if __name__ == '__main__':
    unittest.main()
