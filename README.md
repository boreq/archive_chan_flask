# Archive Chan
Archive Chan is a 4chan archive implemented as a Django application.

![Board view - catalog](screens/readme.png "Board view - catalog")

## Installation
### Required software versions
Application was written with Python 3 and Django 1.6+ in mind. At this point in does not support Python 2.

### Dependencies
This application requires the [requests](http://docs.python-requests.org/en/latest/) package.

### Installing the application
Installation is exactly the same as an installation of any Django application. Simply copy `archive_chan` directory to your project directory and add `archive_chan` to the `INSTALLED_APPS` list in the project settings file.

## Configuration
Application specific settings are located in the `archive_chan/settings.py` file. Instructions on overriding those settings are provided in that settings file.  

Django commands `archive_chan_update` and `archive_chan_remove_old_threads` must be called in regular intervals by CRON or similar daemon. Recommended intervals are about 10-20 minutes and 12-24 hours respectfully.

WARNING: first `archive_chan_update` will take a lot of time to complete because it will have to scrap all threads in the specified boards. You might want to run it manually a couple of times in a row with `--progress` flag to see what is going on. After the command will finally take relatively short time to execute enable CRON and don't worry about it anymore.

## Usage
Settings described here are added through the Django administration panel. You will see a lot of irrelevant tables there with debug mode enabled. You might want to disable it.

First you have to specify the boards which are supposed to be archived. Threads are updated in the specified intervals: script downloads a catalog for all specified boards, checks which threads have to be updated and adds new posts to the database. Old threads will be removed after the time specified in the board settings. Saved threads will be preserved and will not be deleted. You can also specify triggers which will automatically tag or save a thread if specified conditions arise. Logged in users might manually save threads and add or remove tags through the thread view.

## Changing the code
All code improvements are greatly appreciated.  

You have to run `make.py` after changing static JS or CSS files. Required files will be preprocessed, minified and concatenated. This script requires `yui-compressor`, `sass` and `cat`.
