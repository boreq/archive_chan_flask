import datetime
import sys
from flask import current_app
from flask.ext import script
from tendo import singleton
from ..database import db
from ..models import Board, Update
from ..lib.helpers import utc_now
from ..lib.scraper import BoardScraper


class UpdateInfo(object):
    def __init__(self, board):
        self.board = board
        self.start()

    def start(self):
        self.processing_start = utc_now()
        self.update = Update(
            board=self.board,
            start=self.processing_start,
            used_threads=current_app.config['SCRAPER_THREADS_NUMBER']
        )
        db.session.add(self.update)
        db.session.commit()

    def encoutered_error(self, e):
        self.update.status = Update.FAILED

    def end(self, board_scraper):
        try:
            if self.update.status != Update.FAILED:
                self.update.status = Update.COMPLETED

            self.processing_end = utc_now()
            self.processing_time =  self.processing_end - self.processing_start
            self.update.end = self.processing_end

            self.update = board_scraper.stats.add_to_record(
                self.update,
                self.processing_time
            )

        except Exception as e:
            sys.stderr.write('%s\n' % e)

        finally:
            db.session.add(self.update)
            db.session.commit()

        print('%s Board: %s %s' % (
            datetime.datetime.now(),
            self.board,
            board_scraper.stats.get_text(self.processing_time),
        ))


class Command(script.Command):
    """Scraps threads from all active boards.
    This command should be run periodically to download new threads, posts
    and images.
    """

    option_list = (
        script.Option(
            '--progress',
            action='store_true',
            dest='progress',
            help='Display progress.',
        ),
    )

    def run(self, progress):
        # Prevent multiple instances.
        me = singleton.SingleInstance()
        boards = Board.query.filter(Board.active==True).all()

        for board in boards:
            update_info = UpdateInfo(board)
            scraper = BoardScraper(board, progress=progress)

            try:
                scraper.update()

            except Exception as e:
                update_info.encoutered_error(e)
                sys.stderr.write('%s\n' % e)

            finally:
                update_info.end(scraper)
