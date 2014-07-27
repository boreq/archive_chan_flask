# Detailed installation guide

This is a detailed installation guide containing all necessary steps to set everything up from scratch using:

* [NGINX][nginx] - as a web server
* [Gunicorn][gunicorn] -  WSGI HTTP server
* [supervisor][supervisor] - a process control system to keep gunicorn up and running
* [virtualenv][virtualenv] - virtual environment used to separate installed Python packages from the ones globally installed in your system. That way you can safely use many different versions of the same package.
* [PostgreSQL][postgresql] - a database system. I will describe the process for PostgreSQL but it is the same for any database.

Obviously each of those components can be replaced with a different program but that is the set up that I use. I tested all steps on Debian since it has got a large userbase and it is a base for many dustributions. Note that I am going to use long, verbose names for directories to make sure that everything is clear, obviously you can shorten them.

## General idea

    NGINX <---> [ GUNICORN launched by SUPERVISOR in virtualenv ] <---> POSTGRESQL

## What are we going to do?

1. Install Python.
2. Set up virtualenv.
3. Clone the Archive Chan repository.
4. Install packages and gunicorn in the virtualenv.
5. Create Django project.
6. Set up the database.
7. Set up gunicorn and supervisor.
8. Set up nginx.


## 1. Install Python and other Python related programs
### Python
I will not get into detail in this point since there are many tutorials available. Just remember that you need Python 3. To check your Python version run `python --version`.  

Please note that the executable and/or package might be also called `python3` or even end with a more detailed version number. The same is true for `pip` and `virtualenv`. Eg. `python3-pip` or `pip-3.3` and so on.

### pip
`pip` is a tool for installing Python packages easily.  
[Official installation guide][pip_guide].

### virtualenv
`virtualenv` is a tool for creating isolated Python environments.  
[Official installation guide][virtualenv_guide].


## 2. Create virtualenv
Virtualenv can be created anywhere in your file system. I am going to do that in `/var/www/`. You can name your virtualenv in any way you want but you will have to use that name instead of the one chosen by me in the following commands.

    $ virtualenv archive_chan_virtualenv

That command should create a directory called `archive_chan_virtualenv` in the current working directory. If your Python 3 executable is not called `python` then specify it like this:

    $ virtualenv -p python3 archive_chan_virtualenv

If something goes wrong you can delete the virtualenv just as any other directory and create it again.

## 3. Clone the Archive Chan repository
As previously, this directory can be placed anywhere but I will simply clone it to `/var/www/archive_chan` to keep everything in one place:

    $ git clone https://github.com/boreq/archive_chan
    $ ls
    archive_chan archive_chan_virtualenv

Great! We now have two directories: one with the virtual environment files and other with Archive Chan repository.

## 4. Install required packages
### Activate virtualenv
To install the packages inside the virtualenv you have just created you need to enable it first. To do so execute the following command:

    $ source archive_chan_virtualenv/bin/activate

After that you should see the name of your virtualenv in your command prompt. For example: `(archive_chan) user@host:/var/www$`. Now that the virtualenv is activated for this terminal session `python` and `pip` executables you use are those located inside it. That means that all the packages that you will now install using `pip` will be placed in the virtual environment.

I will indicate if the executed command must be run with virtualenv activated by including its name in the parenthesis in front of the command. You don't have to disable it for the commands which are missing that clause but make sure that it is on for those which don't.

You can leave the virtualenv by executing this command:

    (archive_chan_virtualenv) $ deactivate

Of course you can also simply close your terminal. You can try deactivating and activating the virtualenv again now. Remember that the virtualenv is activated separately in each terminal session.

### Install required packages
`pip` can install the packages automatically using the provided `requirements.txt` file. This file is located in the Archive Chan repository.

    (archive_chan_virtualenv) $ pip install -r /path/to/requirements.txt

This will install required packages like Django. You can see all of them by opening this file with a text editor. Some of the defined packages have additional dependencies which will be handled automatically.

### Confirm that everything is fine
You can see a list of installed packages by executing:

    (archive_chan_virtualenv) $ pip list

## 5. Create a Django project
### Create project
Lets enter the virtualenv directory. We will create a project there to keep everything in one place.

    (archive_chan_virtualenv) $ cd archive_chan_virtualenv

Now it is time to create a Django project:

    (archive_chan_virtualenv) $ django-admin.py startproject archive_chan_project
    (archive_chan_virtualenv) $ ls
    archive_chan_project bin include lib

Test that it is working by running a Django dev server:

    (archive_chan_virtualenv) $ archive_chan_project/manage.py runserver

You should see some info and a link to `http://127.0.0.1:8000`. Follow it and you will see the Django's welcome page. Hit `ctrl-c` to stop the server.

### Copy or link the Archive Chan application directory
Enter the created project directory:

    $ cd archive_chan_project
    $ ls
    archive_chan_project manage.py

I am going to create a symlink here to easily access the application directory located in the previously cloned repository. You can simply copy it here instead but that way the future updates will be easier:

    $ ln -s /var/www/archive_chan/archive_chan/ archive_chan
    $ ls
    archive_chan archive_chan_project manage.py

Everything appears to be in order. Lets confirm that:

    $ readlink archive_chan
    /var/www/archive_chan/archive_chan/

### Add application to the Django project
Use your text editor of choice to edit `archive_chan_project/settings.py` file. Add `archive_chan` to the `INSTALLED_APPS`:

    INSTALLED_APPS = (
        ...
        'archive_chan',
    )

Next edit `archive_chan_project/urls.py` file. Add the following line to the `urlpatterns`:

    urlpatterns = patterns('',
        url(r'^', include('archive_chan.urls', namespace='archive_chan')),
        ...
    )

Run the dev server:

    (archive_chan_virtualenv) ./manage.py runserver

Open the website again. The error page should be displayed since the database has not been created yet.

## 6. Set up the database

I am going to use PostgreSQL. Steps are similar for other databases. You can read the [official Django installation guide][django_database_installation]. There is also [a separate page about databases][django_database].

### Actually install the database
Use your distribution's package manager. The Debian package is called `postgresql`.

[Debian guide][postgresql_guide].

### Configure the database
Follow [the Debian wiki][postgresql_guide_user] to create a new database called `archive_chan`. You can create a new user or use an existing one. I will just use the user `postgres` since I don't need to actually handle the user privileges:

    $ sudo su postgres
    $ psql
    postgres=# \password
    postgres=# CREATE DATABASE archive_chan TEMPLATE template0;
    postgres=# GRANT ALL PRIVILEGES ON DATABASE archive_chan TO postgres;
    postgres=# \q
    $ exit

I changed the password, created a database, granted database privileges to the user, left the `psql` and got back to my real user.

### Add Python database bindings
You will also need a package to communicate with your database. It is not included in `requirements.txt` since basically any database supported by Django will be fine and they require different packages. For PostgreSQL you can use `psycopg2` package:

    (archive_chan_virtualenv) $ pip install psycopg2

More info is available in the [official Django installation guide][django_database_installation] linked previously.

WARNING: You might need PostgreSQL development lib for that. It should be called `libpq-dev` in Debian/Ubuntu or something like `postgresql-devel` on other distributions. Install it like any other program with your distribution package manager (`apt-get`, `pacman` etc). The same goes for `build-essential` since you may need `gcc` compiler. In case of trouble using Bing (TM) to look for an error code will definitely provide a simple solution to your issue.

### Set the correct settings
Edit `archive_chan_project/settings.py`. Change `DATABASES` to:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'archive_chan', # The name of the database you created
            'USER': 'postgres',     # The user you created (I went with the default one)
            'PASSOWRD': 'password', # Database password you set for that user
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

### Tell Django to create all necessary tables

    (archive_chan_virtualenv) $ ./manage.py syncdb

You will be asked to create a superuser. Superuser has got a full access to the Django administration panel. Respond with `yes`.

### See the results

Run the dev server again.

    (archive_chan_virtualenv) ./manage.py runserver

You will be greeted with a blank Archive Chan page - you have not designated any boards to be scrapped yet. Great success, but we still need an actual web server.

## 7. Set up gunicorn and supervisor
### Create a new user
You can also run everything as your normal user but I think that it is better to separate everything if possible.
[User creation guide][user_creation_guide]. I created a user called `python-server`. `chown` everything to your new created user:

    $ cd /var/www/archive_chan_virtualenv
    $ chown -R python-server *

### Install gunicorn
Now you have to install gunicorn. It is not really a required package but rather a server with many alternatives available so it is not included in the `requirements.txt`:

    (archive_chan_virtualenv) $ pip install gunicorn

### Create a script to launch gunicorn
Lets call this script `run` and place it in the virtualenv directory:

    #!/bin/bash
    cd /var/www/archive_chan_virtualenv/archive_chan_project/
    source ../bin/activate
    gunicorn -w 3 -b 127.0.0.1:8000 -u python-server archive_chan_project.wsgi:application

Check if the script is in the correct directory and add an execute permission:

    $ cd /var/www/archive_chan_virtualenv
    $ ls
    archive_chan_project bin include lib run
    $ chmod +x run

See `gunicorn --help` for more flags and information about the ones I used. You can run the line starting with `gunicorn` directly from the terminal to test the config.

Execute the script as your user (or yourself if you have not created a new one):

    $ sudo -u python-server ./run

You should see no output. Go to the `localhost:8000` in your browser. The Archive Chan page without any CSS styling should appear. That is because there is no web server to handle the static CSS and JS files yet. Kill the script with `ctrl-c`.

### Install supervisor
Use your distribution's package manager. The Debian package is called `supervisor`.

### Configure supervisor
Create the file `/etc/supervisor/conf.d/archive_chan`:

    $ cat /etc/supervisor/conf.d/archive_chan

    [program:archive_chan]
    directory = /var/www/archive_chan_virtualenv
    user = python-server
    command = /var/www/archive_chan_virtualenv/run
    stdout_logfile = /var/www/archive_chan_virtualenv/log/supervisor.log
    stderr_logfile = /var/www/archive_chan_virtualenv/log/supervisor.error.log

To be sure reaload everything:

    # supervisorctl reread
    # supervisorctl update

Refresh `localhost:8000` in the browser. You should see a page without CSS styles again. If supervistor did not start the new task automatically try:

    # supervisorctl restart archive_chan

Help can be displayed like this:

    # supervisorctl help

Almost done. We just need a web server now.

## 8. Set up nginx
### Prepare your Django project
We need to set a few things first. Add the following values to `archive_chan_project/settings.py` file (or edit the existing ones):

    STATIC_URL = '/static/'
    STATIC_ROOT = '/var/www/public_html/static/'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = '/var/www/public_html/media/'

Create the directories and change the owner to `python-server` (or the user that you used earlier):

    # mkdir -p /var/www/public_html/static
    # mkdir -p /var/www/public_html/media
    # chown -R python-server:www-data /var/www/public_html
    $ ls /var/www/public_html
    media static

`www-data` is a user used by nginx so the web server will have read access in those directories.

Now we will make Django copy all static files to the directory `/var/www/public_html/static` which we created:

    $ cd /var/www/archive_chan_virtualenv/archive_chan_project
    $ sudo su python-server
    $ source ../bin/activate
    (archive_chan_virtualenv) $ ./manage.py collectstatic

Confirm with `yes`. You can see if there are new files in the `/var/www/public_html/static/` directory.

### Install nginx
Use your distribution's package manager. The Debian package is called `nginx`.

### Configure nginx
Create file `/etc/nginx/sites-available/archive_chan`:

    server {
      listen 80;
      server_name localhost;

      location /static/ {
        alias /var/www/public_html/static/;
      }

      location /media/ {
        alias /var/www/public_html/media/;
      }

      location / {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      }
    }

Server name should be set to server's IP address or the domain name. Since we only have one server everything is handled by that server block by default and this setting doesn't really matter but it is important to remember to set that value correctly to make if future proof.

The `/static/` and `/media/` location blocks are used to bypass Django and serve the static files and images directly. Remember to include `/` at the end of the path or it will not work (or remove it from both location definition and path). nginx is not intelligent in connecting paths, it simply concats strings.

Since nginx actually loads files located in the `sites-enabled` directory we need to create a link to the config file. We also need to get rid of the linked `default` configuration file which also listens on `localhost`:

    $ cd /etc/nginx/sites-enabled
    # ln -s /etc/nginx/sites-available/archive_chan archive_chan
    # rm default

Reload the nginx configuration with:

    # service nginx reload

I think my server was not running so I had to use:

    # service nginx restart

Navigate to `http://localhost` in your browser. You should see the blank archive chan page with CSS styles available again. This time it is a fully functional website which could actually be used in production.

## 9. Final configuration.
### Correct settings
Edit `archive_chan_project/settings.py` and disable `DEBUG`:

    DEBUG = False
    TEMPLATE_DEBUG = False
    ALLOWED_HOSTS = ['localhost']

You need to order `supervisor` to restart the script which runs `gunicorn` after each change like that:

    # supervisorctl restart archive_chan

### Add boards
Go to `http://localhost/admin/` and login with the username and password which you created while running `manage.py syncdb`. Create the boards you want to monitor.

### Test
Run:

    $ cd /var/www/archive_chan_virtualenv/archive_chan_project
    $ sudo su python-server
    $ source ../bin/activate
    (archive_chan_virtualenv) $ ./manage.py archive_chan_update --progress

You can actually wait for it to finish. You should notice new threads appearing one by one on the website.

### Set up cron
We want the archive to automatically update periodically.

Create two scripts.

``/var/www/archive_chan_virtualenv/update` to download new threads:

    #!/bin/bash
    cd /var/www/archive_chan_virtualenv/archive_chan_project
    source ../bin/activate
    ./manage.py archive_chan_update

``/var/www/archive_chan_virtualenv/delete` to remove old threads:

    #!/bin/bash
    cd /var/www/archive_chan_virtualenv/archive_chan_project
    source ../bin/activate
    ./manage.py archive_chan_remove_old_threads

Change the owner of those scripts to `python-server` with `chown` and add the execution permission with `chmod`.

Set up cron to run them periodically by adding this to your `/etc/crontab`:

    */10 * * * * python-server /var/www/archive_chan_virtualenv/update
    5 */2 * * * python-server /var/www/archive_chan_virtualenv/delete

First command will run every 10 minutes and the second one every 2 hours.

[nginx]: http://nginx.com/
[gunicorn]: http://gunicorn.org
[supervisor]: http://supervisord.org/
[virtualenv]: https://virtualenv.pypa.io/en/latest/
[postgresql]: http://www.postgresql.org/

[pip_guide]: https://pip.pypa.io/en/latest/installing.html
[virtualenv_guide]: http://virtualenv.readthedocs.org/en/latest/virtualenv.html#installation
[django_database_installation]: https://docs.djangoproject.com/en/dev/topics/install/#get-your-database-running
[django_database]: https://docs.djangoproject.com/en/dev/ref/databases/
[postgresql_guide]: https://wiki.debian.org/PostgreSql
[postgresql_guide_user]:https://wiki.debian.org/PostgreSql#User_access
[user_creation_guide]: https://wiki.debian.org/AccountHandlingInMaintainerScripts
