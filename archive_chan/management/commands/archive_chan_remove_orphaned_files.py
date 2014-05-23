from os import path, listdir, remove
from optparse import make_option
import datetime

from django.core.management.base import BaseCommand
from archive_chan.models import Image
from django.conf import settings

class Command(BaseCommand):
    args = ''
    help = 'Remove orphaned files - files without a corresponding database entry. In theory they should be deleted automatically but who knows. WARNING: this is a dumb function which will simply iterate and query the database once for each file. It can really strain your server.' 
    option_list = BaseCommand.option_list + (
        make_option(
            '--progress',
            action="store_true",
            dest='progress',
            help='Display progress.',
        ),
    )


    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.files_deleted = 0
        self.thumbnails_deleted = 0


    def handle(self, *args, **options):
        processing_start = datetime.datetime.now()

        self.files_deleted = self.process_directory('post_images', self.image_exists_in_db, options['progress'])
        self.thumbnails_deleted = self.process_directory('post_thumbnails', self.thumbnail_exists_in_db, options['progress'])

        processing_time = datetime.datetime.now() - processing_start

        print('%s Time passed: %s sec Deleted images: %s Deleted thumbnails: %s' % (datetime.datetime.now(), processing_time.seconds, self.files_deleted, self.thumbnails_deleted))


    def process_directory(self, upload_to_directory, check_in_db_function, show_progress):
        """Search for orphaned files and remove them."""
        files_deleted = 0

        dir_path = path.join(settings.MEDIA_ROOT, upload_to_directory)

        if path.isdir(dir_path):
            for (index, filename) in enumerate(listdir(dir_path)):
                # Just info.
                if show_progress:
                    print('%s - %s' % (index, filename))

                full_path = path.join(dir_path, filename)

                # Check if this is a file or a directory.
                if path.isfile(full_path):
                    # Remove image.
                    if not check_in_db_function(path.join(upload_to_directory, filename)):
                        try:
                            remove(full_path)
                            files_deleted += 1

                        except:
                            pass

        return files_deleted


    def image_exists_in_db(self, upload_to_path):
        return Image.objects.filter(image=upload_to_path).exists()


    def thumbnail_exists_in_db(self, upload_to_path):
        return Image.objects.filter(thumbnail=upload_to_path).exists()
