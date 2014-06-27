from django.db.models import Max, Min, Count
from django.core.management.base import BaseCommand

from archive_chan.models import Thread

class Command(BaseCommand):
    args = ''
    help = 'Recount the data in the thread model.'

    def handle(self, *args, **options):
        threads = Thread.objects.annotate(
            correct_first_reply=Min('post__time'),
            correct_last_reply=Max('post__time'),
            correct_replies=Count('post'),
            correct_images=Count('post__image')
        )

        total = 0
        updated = 0

        for thread in threads:
            if (thread.correct_first_reply != thread.first_reply
                or thread.correct_last_reply != thread.last_reply
                or thread.correct_replies != thread.replies
                or thread.correct_images != thread.images):

                thread.first_reply = thread.correct_first_reply
                thread.last_reply = thread.correct_last_reply
                thread.replies = thread.correct_replies
                thread.images = thread.correct_images

                thread.save()

                updated += 1

            total += 1

            print('Total: %s Updated: %s' % (total, updated))
