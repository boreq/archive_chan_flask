import datetime, json

from django.core.urlresolvers import reverse
from django.db import connection
from django.test import TestCase
from django.test.client import Client
from django.utils.timezone import utc

import archive_chan.lib.modifiers as modifiers
import archive_chan.models as models
import archive_chan.lib.scraper as scraper

now = datetime.datetime(2014, 4, 23, 15, 0, 0, 0, utc)

class SimpleFilterTest(TestCase):
    def setUp(self):
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


class SimpleSortTest(TestCase):
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


class ViewsTest(TestCase):
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


class ApiTest(TestCase):
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

class TriggersTest(TestCase):
    def setUp(self):
        board = models.Board.objects.create(name='a')
        self.thread = models.Thread.objects.create(
            board=board,
            number=1,
            first_reply=now,
            last_reply=now
        )

        self.post_json = {
            'no': 1,
            'time': 123,
            'name': 'name',
            'trip': 'trip',
            'email': 'email',
            'sub': 'sub',
            'com': 'com',
            'tim': 'tim',
            'ext': 'ext',
            'filename': 'filename',
        }

    def insert_triggers(self):
        """Create all possible combinations of a trigger."""
        self.phrases = []

        for field_choice in dict(models.Trigger.FIELD_CHOICES).keys():
            for event_choice in dict(models.Trigger.EVENT_CHOICES).keys():
                for post_type_choice in dict(models.Trigger.POST_TYPE_CHOICES).keys():
                    for case_sensitive in [True, False]:
                        phrase = ('%s-%s-%s-%s' % (
                                field_choice,
                                event_choice,
                                post_type_choice,
                                str(case_sensitive),
                            ))

                        self.phrases.append(phrase)

                        tag = models.Tag.objects.create(name=phrase)

                        models.Trigger.objects.create(
                            field=field_choice,
                            event=event_choice,
                            post_type=post_type_choice,
                            case_sensitive=case_sensitive,
                            phrase=phrase,
                            tag_thread=tag
                        )


    def test_no_triggers(self):
        triggers = scraper.Triggers()
        post_data = scraper.PostData(self.post_json)

        actions = triggers.get_actions(self.thread, post_data)
        self.assertEqual(len(actions), 0)

    def test_triggers(self):
        """Just run all triggers on the default post to look for exceptions."""
        self.insert_triggers()

        triggers = scraper.Triggers()
        post_data = scraper.PostData(self.post_json)
        actions = triggers.get_actions(self.thread, post_data)

        # 2(isnot/containsno) * 2(any/master) * 5(fields) * 2(casesensitivity)
        # any/master included for 2 because each trigger has a separate tag
        self.assertEqual(len(actions), 40)

    def test_triggers_detailed(self):
        # Change the fields to match triggers one by one and try to break something.
        triggers = scraper.Triggers()

        for field_choice in dict(models.Trigger.FIELD_CHOICES).keys():
            for event_choice in dict(models.Trigger.EVENT_CHOICES).keys():
                for post_type_choice in dict(models.Trigger.POST_TYPE_CHOICES).keys():
                    for case_sensitive in [True, False]:
                        phrase = ('%s-%s-%s-%s' % (
                                field_choice,
                                event_choice,
                                post_type_choice,
                                str(case_sensitive),
                            ))

                        fields = {
                            'name': 'name',
                            'trip': 'trip',
                            'email': 'email',
                            'subject': 'sub',
                            'comment': 'com',
                        }

                        json_data = self.post_json.copy()
                        json_data[fields[field_choice]] = phrase

                        post_data = scraper.PostData(json_data)
                        actions = triggers.get_actions(self.thread, post_data)
