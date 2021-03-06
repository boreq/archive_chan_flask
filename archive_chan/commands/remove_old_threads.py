from datetime import datetime, timedelta
from flask.ext import script
from ..database import db
from ..models import Board, Thread
from ..lib.helpers import utc_now


class Command(script.Command):
    """Removes unsaved threads older than the maximum thread age for each board.
    This command should be run periodically to clean the database.
    """

    def run(self):
        boards = Board.query.filter(Board.store_threads_for>0).all()

        for board in boards:
            processing_start = datetime.now()

            # Get the posts older than specified in the board settings.
            time_threshold =  utc_now() - timedelta(hours=board.store_threads_for)
            queryset = Thread.query.filter(
                Thread.board==board,
                Thread.last_reply<time_threshold,
                Thread.saved==False
            )

            # Count for stats and delete.
            amount = queryset.count()

            # Bulk delete will not trigger Python cascades and the files must
            # be deleted from the HDD so normal db based cascade can't be used.
            threads = queryset.all()
            for thread in threads:
                db.session.delete(thread)
                db.session.commit()

            processing_time = datetime.now() - processing_start

            print('%s Board: %s Deleted threads: %s Time passed: %s sec' % (
                datetime.now(),
                board,
                amount,
                processing_time.seconds
            ))
