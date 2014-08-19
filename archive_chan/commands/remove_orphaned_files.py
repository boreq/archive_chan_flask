import datetime
from os import path, listdir, remove
from flask import current_app
from flask.ext import script
from ..models import Image

class Command(script.Command):
    """Removes the files without a corresponding database entry. In theory those
    files should be deleted automatically but who knows what can happen.
    WARNING: this is a dumb function which will simply iterate over all files
    and query the database once for each file so it can strain your server.
    """

    option_list = (
        script.Option(
            '--progress',
            action='store_true',
            dest='progress',
            help='Display progress.',
        ),
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.files_deleted = 0
        self.thumbnails_deleted = 0

    def run(self, progress):
        processing_start = datetime.datetime.now()

        self.files_deleted = self.process_directory(
            'post_images',
            self.image_exists_in_db,
            progress
        )
        self.thumbnails_deleted = self.process_directory(
            'post_thumbnails',
            self.thumbnail_exists_in_db,
            progress
        )

        processing_time = datetime.datetime.now() - processing_start

        print('%s Time passed: %s sec Deleted images: %s Deleted thumbnails: %s' % (
            datetime.datetime.now(),
            processing_time.total_seconds(),
            self.files_deleted,
            self.thumbnails_deleted)
        )

    def process_directory(self, directory, check_in_db_function, show_progress):
        """Search for orphaned files and remove them."""
        files_deleted = 0

        dir_path = path.join(current_app.config['MEDIA_ROOT'], directory)

        if path.isdir(dir_path):
            for (index, filename) in enumerate(listdir(dir_path)):
                if show_progress:
                    print('%s - %s' % (index, filename))
                full_path = path.join(dir_path, filename)
                if path.isfile(full_path):
                    if not check_in_db_function(path.join(directory, filename)):
                        try:
                            remove(full_path)
                            files_deleted += 1
                        except:
                            pass
        return files_deleted

    def image_exists_in_db(self, path):
        return Image.query.filter(Image.image==path).first() is not None

    def thumbnail_exists_in_db(self, path):
        return Image.query.filter(Image.thumbnail==path).first() is not None
