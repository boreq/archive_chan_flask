import datetime, sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from tendo import singleton

from archive_chan.models import Board
from archive_chan.lib.scraper import BoardScraper
from archive_chan.settings import AppSettings

class Command(BaseCommand):
    args = ''
    help = 'Scraps threads from all active boards. This command should be run periodically to download new threads, posts and images.'
    option_list = BaseCommand.option_list + (
        make_option(
            '--progress',
            action="store_true",
            dest='progress',
            help='Display progress.',
        ),
    )


    def handle(self, *args, **options):
        # Prevent multiple instances. Apparently fcntl.lockf is very useful and does completely nothing.
        me = singleton.SingleInstance()

        boards = Board.objects.filter(active=True)

        # Show progress?
        if options['progress']:
            progress = True
        else:
            progress = False

        # Get new data for each board.
        for board in boards:
            scraper = BoardScraper(board, progress=progress)

            processing_start = datetime.datetime.now()

            # Actual update.
            try:
                scraper.update()

            except Exception as e:
                raise
                sys.stderr.write('%s\n' % (e))

            # Everything below is just info.
            processing_time = datetime.datetime.now() - processing_start

            print('\nBoard: %s %s' % (
                board,
                scraper.stats.get_text(processing_time),
            ))
