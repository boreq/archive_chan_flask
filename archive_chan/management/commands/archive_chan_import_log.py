from datetime import datetime
import sys, re
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import utc

from archive_chan.models import Update, Board
from archive_chan.settings import AppSettings

class Command(BaseCommand):
    args = '<file_path file_path ...>'
    help = 'Imports data from scraper log files.'
    option_list = BaseCommand.option_list + (
        make_option(
            '-t',
            '--used-threads',
            action="store",
            dest='used_threads',
            help='Specify the number of threads to set in the database. Log does not contain that data.',
        ),
    )

    def handle(self, *args, **options):
        boards = {}

        if options['used_threads'] is None:
            raise ValueError('Specify the number of used threads.')

        options['used_threads'] = int(options['used_threads'])

        sucessful = 0
        failed = 0
        added = 0

        for file_path in args:
            try: 
                with open(file_path) as f:
                    for line in f:
                        try:
                            line = re.sub('[^a-zA-Z0-9\.\-: ]', '', line.strip()).split()

                            data = {
                                'date': datetime.strptime( '%s %s' % (line[0], line[1]), '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=utc),
                                'board': line[3].replace('/',''),
                                'total_time': float(line[6]),
                                'wait_time': float(line[6]) * float(line[8]) / 100,
                                'download_time': float(line[6]) * float(line[10]) / 100,
                                'processed_threads': int(line[15]),
                                'added_posts': int(line[18]),
                                'removed_posts': int(line[21]),
                                'downloaded_images': int(line[24]),
                                'downloaded_thumbnails': int(line[27]),
                                'downloaded_threads': int(line[30]),
                                'used_threads': options['used_threads'],
                            }

                            if not data['board'] in boards:
                                boards[data['board']] = Board.objects.get(name=data['board'])
                            data['board'] = boards[data['board']]

                            update, created = Update.objects.get_or_create(**data)

                            if created:
                                added += 1

                            sucessful += 1

                            print('Successful: %s Added: %s Failed %s' % (sucessful, added, failed))

                        except (ValueError, IndexError) as e:
                            failed += 1
                            sys.stderr.write('%s\n' % e)

            except FileNotFoundError as e:
                sys.stderr.write('%s\n' % e)
