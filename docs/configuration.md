### Required software versions
Application was written with Python 3.3+ in mind. At this point it does not
support Python 2.


# Configuration
This is the basic installation and configuration guide for users experienced
with web applications running on Flask, Django or similar frameworks.


## Settings
Default settings are located in `archive_chan/settings.py` file. Create a new
file anywhere and name it `settings.py`. Copy and modify the values which you
want to change to that file. This is the minimal configuration, check the
default `settings.py` for more detailed information:

    SECRET_KEY = 'your_random_secret_key'
    SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/archive_chan'
    MEDIA_ROOT = '/path/to/a/directory/with/image/files/'

You have to run your WSGI server with the path to that settings file set in the
`ARCHIVE_CHAN_SETTINGS` environment variable. Use the `export` command to do so
 in your process management system, service file, script etc:

    export ARCHIVE_CHAN_SETTINGS=/path/to/new/settings.py


## Database
To create all required database tables run `script`.


## Deployment
[Official Flask deployment guide](http://flask.pocoo.org/docs/0.10/deploying/).

Application object is created in `runserver.py` and called `app`. Example:

    cd archive_chan_repository
    gunicorn runserver:app

You have to directly serve static files located in `archive_chan/static/`
directory under `/static/` url and image files located in your `MEDIA_ROOT` under
`/media/`.


## Usage
First create a new user to gain access to the admin panel:

    python run.py create_user

After that go to the website, login and enter the admin panel. All actions
described in this section are performed in it.

First you have to add the boards which are supposed to be archived. Threads
are updated in the specified intervals: script downloads a catalog for each of
the specified boards, checks which threads have to be updated and adds new
posts to the database. Old threads will be removed after the time specified
in the board settings. Saved threads will be preserved and will not be deleted.
You can also specify triggers which will automatically tag or save a thread if
specified conditions arise. Logged in users might manually save threads and add
or remove tags through the thread view.


## Cron
Commands `update` and `remove_old_threads` must be called in regular intervals
by CRON or similar daemon. Recommended intervals are about 10-20 minutes and
1-2 hours respectfully. Commands are launched like that:

    python run.py update
    python run.py remove_old_threads

First `update` will take a lot of time to complete because it will
have to scrap all threads in the specified boards. You might want to run it
manually a couple of times in a row with `--progress` flag to see what is going
on. After the command will finally take relatively short time to execute enable
CRON and don't worry about it anymore. There is an example script to be used
with cron in the same directory as this file.
