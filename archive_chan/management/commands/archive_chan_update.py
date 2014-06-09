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
                sys.stderr.write('%s\n' % (e))

            # Everything below is just info.
            processing_time = datetime.datetime.now() - processing_start

            try:
                wait_percent = round(scraper.total_wait / processing_time.seconds * 100)
                downloading_percent = round(scraper.total_download_time / processing_time.seconds * 100)

            except:
                # Division by zero. Set 0 for the statistics.
                wait_percent = 0
                downloading_percent = 0

            print('%s Board: %s Time passed: %s seconds (%s%% waiting, %s%% downloading files) Processed threads: %s Added posts: %s Removed posts: %s Downloaded images: %s Downloaded thumbnails: %s Downloaded threads: %s' % (
                datetime.datetime.now(),
                scraper.board,
                processing_time.seconds,
                wait_percent,
                downloading_percent,
                scraper.stats.get('processed_threads'),
                scraper.stats.get('added_posts'),
                scraper.stats.get('removed_posts'),
                scraper.stats.get('downloaded_images'),
                scraper.stats.get('downloaded_thumbnails'),
                scraper.stats.get('downloaded_threads')
            ))
