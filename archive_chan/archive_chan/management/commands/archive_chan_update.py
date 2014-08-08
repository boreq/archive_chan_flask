import datetime, sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import utc

from tendo import singleton

from archive_chan.models import Board, Update
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
            # Info.
            processing_start = datetime.datetime.utcnow().replace(tzinfo=utc)
            update = Update.objects.create(board=board, start=processing_start, used_threads = AppSettings.get('SCRAPER_THREADS_NUMBER'))

            try:
                # Actual update.
                scraper = BoardScraper(board, progress=progress)
                scraper.update()

                # Info.
                update.status = Update.COMPLETED

            except Exception as e:
                sys.stderr.write('%s\n' % (e))

            finally:
                # Info.
                try:
                    if update.status != Update.COMPLETED:
                        update.status = Update.FAILED

                    processing_end = datetime.datetime.utcnow().replace(tzinfo=utc)
                    processing_time =  processing_end - processing_start
                    update.end = processing_end
                    update = scraper.stats.add_to_record(update, processing_time)

                except Exception as e:
                    sys.stderr.write('%s\n' % (e))

                finally:
                    update.save()

                # Everything below is just info.
                print('%s Board: %s %s' % (
                    datetime.datetime.now(),
                    board,
                    scraper.stats.get_text(processing_time),
                ))
