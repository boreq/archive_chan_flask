import datetime

from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils.timezone import utc
from django.core.signals import Signal

from archive_chan.models import Board, Thread, Post, post_post_delete
from django.db.models.signals import post_delete

class Command(BaseCommand):
    args = ''
    help = 'Remove old, unsaved threads. This command should be run periodically to clean the database.'

    def handle(self, *args, **options):
        boards = Board.objects.filter(store_threads_for__gt=0)

        for board in boards:
            processing_start = datetime.datetime.now()

            # Get the posts older than the amount specified in the board settings.
            time_threshold = datetime.datetime.now().replace(tzinfo=utc) - datetime.timedelta(hours=board.store_threads_for)
            queryset = Thread.objects.filter(board=board, last_reply__lt=time_threshold, saved=False)

            # Count for stats and delete.
            amount = queryset.count()

            post_delete.disconnect(receiver=post_post_delete, sender=Post)

            try:
                queryset.delete()

            except Exception as e:
                sys.stderr.write('%s\m' % (e))

            finally:
                post_delete.connect(post_post_delete, sender=Post)

            processing_time = datetime.datetime.now() - processing_start

            print('%s Board: %s Deleted threads: %s Time passed: %s sec' % (datetime.datetime.now(), board, amount, processing_time.seconds))
