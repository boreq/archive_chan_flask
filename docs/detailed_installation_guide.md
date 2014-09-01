# Detailed installation guide

This is a detailed installation guide containing all necessary steps to set
everything up from scratch using:

* [NGINX][nginx] - as a web server
* [Gunicorn][gunicorn] - WSGI HTTP server
* [supervisor][supervisor] - process control system to keep gunicorn running
* [virtualenv][virtualenv] - virtual environment used to separate Python packages
* [PostgreSQL][postgresql] - database system.

Each of those components can be replaced with a different program but that is
the set up that I use. I tested all steps on Debian since it has got a large
userbase and it is a base for many distributions. Note that I am going to use
long, verbose names for directories to make sure that everything is clear, you
can change them at will.


## General idea

    NGINX <---> GUNICORN <---> ARCHIVE CHAN <---> POSTGRESQL

NGINX will be used as a main web server. It will directly serve static files
like JS, CSS and images and proxy the rest of the traffic to Gunicorn running
Archive Chan. Required packages will be installed in a virtualenv to avoid
installing them globally on your system.


## What are we going to do?
1. Install Python and related programs.
2. Set up virtualenv.
3. Clone the repository.
4. Install packages and Gunicorn in created virtualenv.
5. Set up the database.
6. Set up gunicorn and supervisor.
7. Set up NGINX.


## 1. Install Python and other Python related programs
### Python
I will not get into detail in this point since there are many tutorials
available. Just remember that you need Python 3. To check your Python version
run `python --version`.

### pip
`pip` is a tool for installing Python packages easily.
[Official installation guide][pip_installation].

### virtualenv
`virtualenv` is a tool for creating isolated Python environments.
[Official installation guide][virtualenv_installation].


## 2. Create virtualenv
In case of problems refer to the [official documentation][virtualenv_docs].

I am going to create a virtualenv called `archive_chan_virtualenv` in
`/var/www/archive_chan/`.

    $ cd /var/www/archive_chan/
    $ virtualenv archive_chan_virtualenv

That command should create a directory called `archive_chan_virtualenv` in the
current working directory. If your Python 3 executable is not called `python`
then specify it like this:

    $ virtualenv -p python3 archive_chan_virtualenv

If something goes wrong you can delete the virtualenv just like any other
directory and create it again.


## 3. Clone the repository
I will clone the repository to previously created `/var/www/archive_chan/`:

    $ git clone https://github.com/boreq/archive_chan_flask.git
    $ ls
    archive_chan_flask archive_chan_virtualenv

We now have two directories: one with the virtual environment files and the
other with Archive Chan repository.


## 4. Install required packages
### Activate virtualenv
To install packages inside the virtualenv which you have just created you need
to enable it first. To do so execute the following command:

    $ source archive_chan_virtualenv/bin/activate

After that you should see the name of your virtualenv in your command prompt.
Now all the packages installed using `pip` will be placed in the virtual
environment.

### Install required packages
`pip` can install the packages automatically using the provided
`requirements.txt` file. This file is located in the Archive Chan repository.

    (archive_chan_virtualenv) $ pip install -r /path/to/requirements.txt

This will install required packages like Flask and needed Flask extensions.
You can see all of them by opening this file with a text editor. Some of the
packages have additional dependencies which will be handled automatically.

### Confirm that everything is fine
You can see a list of installed packages by executing:

    (archive_chan_virtualenv) $ pip list


## 6. Set up the database

I am going to use PostgreSQL. Steps are similar for other databases.

### Actually install the database
Use your distribution's package manager. Debian package is called`postgresql`.

[Debian guide][postgresql_guide].

### Configure the database
Follow [the Debian wiki][postgresql_guide_user] to create a new database called
`archive_chan`. You can create a new user or use an existing one. I will just
use the user `postgres` since I don't actually need to handle the user
privileges in this tutorial:

    $ sudo su postgres
    $ psql
    postgres=# \password
    postgres=# CREATE DATABASE archive_chan TEMPLATE template0;
    postgres=# GRANT ALL PRIVILEGES ON DATABASE archive_chan TO postgres;

I changed the password, created a database and granted database privileges to
the user.

### Add Python database bindings
You will also need a package to communicate with your database. It is not
included in `requirements.txt` since basically any supported database requires
a different package. For PostgreSQL you can use `psycopg2` package:

    (archive_chan_virtualenv) $ pip install psycopg2

You might need PostgreSQL development lib for that. It should be called
`libpq-dev` on Debian/Ubuntu or something like `postgresql-devel` on other
distributions. Install it like any other package with your distribution's
package manager (`apt-get`, `pacman` etc).

### Configure the archive
You can read the configuration guide available in the same directory as this
one. Right now you want to perform steps described in the "Settings" and
"Database" sections in order to write a configuration file and create necessary
tables in the database. Create a file called `settings.py` in
`/var/www/archive_chan`:

    $ cd /var/www/archive_chan
    $ ls
    archive_chan_flask archive_chan_virtualenv settings.py

You can set your media root to `/var/www/archive_chan/media/`, remember to
create that directory.

### See the results
Run the development server to confirm that everything is working:

    (archive_chan_virtualenv) $ export ARCHIVE_CHAN_SETTINGS=/var/www/archive_chan/settings.py
    (archive_chan_virtualenv) $ python runserver.py

Navigate to [127.0.0.1:5000](http://127.0.0.1:5000).You will be greeted with
a blank Archive Chan page - you have not designated any boards to be scrapped
yet. If you see an error it is probably caused by missing Python packages.
Great success, but we still need an actual web server.

## 7. Set up gunicorn and supervisor
### Create a new user
You can run everything as your normal user but I think that it is better to
use a separate user for a server whenever possible.
[Here is the user creation guide][user_creation_guide]. I created a user called
`python-server`. Change the owner of everything in `/var/www/archive_chan`
to your new created user:

    $ chown -R python-server /var/www/archive_chan/

### Install gunicorn
Now you have to install gunicorn. It is not really a required package but rather
 a server with many alternatives available so it is not included in the
 `requirements.txt`:

    # su python-server
    $ source /var/www/archive_chan/archive_chan_virtualenv/bin/activate
    (archive_chan_virtualenv) $ pip install gunicorn

### Create a script to launch gunicorn
Lets call this script `run_gunicorn` and place it in `/var/www/archive_chan/`:

    #!/bin/bash
    cd /var/www/archive_chan/archive_chan_flask/
    source ../archive_chan_virtualenv/bin/activate
    gunicorn -w 3 -b 127.0.0.1:8000 -u python-server runserver:app

See `gunicorn --help` for more flags and information about the ones that I have
used. Check if the script is in the correct directory and add execute permission
to it:

    $ cd /var/www/archive_chan
    $ ls
    archive_chan_flask archive_chan_virtualenv media run_gunicorn settings.py
    $ chmod u+x run_gunicorn

### Install supervisor
Use your distribution's package manager. Debian package is called `supervisor`.

### Configure supervisor
Create a file `/etc/supervisor/conf.d/archive_chan.conf`:

    [program:archive_chan]
    directory = /var/www/archive_chan
    user = python-server
    command = /var/www/archive_chan/run_gunicorn
    stdout_logfile = /var/www/archive_chan/log/supervisor.log
    stderr_logfile = /var/www/archive_chan/log/supervisor.error.log
    environment=ARCHIVE_CHAN_SETTINGS="/var/www/archive_chan/settings.py"

To be sure reload everything:

    # supervisorctl reread
    # supervisorctl update

Refresh `localhost:8000` in the browser. You should see a page without CSS
styles again. If supervistor did not start the new task automatically try:

    # supervisorctl restart archive_chan

Help can be displayed like this:

    # supervisorctl help

Go to the [localhost:8000](http://localhost:8000) in your browser. Archive Chan
page should appear. Now we just need a web server to handle the static files
instead of serving them with Flask.


## 8. Set up NGINX
### Install NGINX
Use your distribution's package manager. Debian package is called `nginx`.

### Configure nginx
Create file `/etc/nginx/sites-available/archive_chan`:

    server {
      listen 80;
      server_name localhost;

      location /static/ {
        # Path to the static files directory.
        # (you can create a symlink somewhere to make is shorter)
        alias /var/www/archive_chan/archive_chan_flask/archive_chan/static/;
      }

      location /media/ {
        alias /var/www/archive_chan/media/;
      }

      location / {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      }
    }

Server name should be set to server's IP address or the domain name. Since we
only have one server everything is handled by that server block by default and
this setting doesn't really matter but it is important to remember to set that
value correctly to make if future proof. By default the last server block is...
well default, but it can be explicitly set by adding `default-server` after
the port number in the `listen` line (probably because the ordering is clear
in one config file eg. `/etc/nginx/nginx.conf` but it gets messy if multiple
config files are loaded).

The `/static/` and `/media/` location blocks are used to bypass Archive Chan
and serve the static files and images directly. Remember to include `/` at the
end of the path or it will not work (or remove it from both location definition
and path). NGINX is not intelligent in connecting paths, it simply concatenates
strings.

Since NGINX actually loads files located in the `sites-enabled` directory we
need to create a link to the config file. We also need to remove the linked
`default` configuration file which also listens on `localhost`:

    $ cd /etc/nginx/sites-enabled
    # ln -s /etc/nginx/sites-available/archive_chan archive_chan
    # rm default

Reload the nginx configuration with:

    # service nginx reload

I think my server was not running so I had to use:

    # service nginx restart

Navigate to [http://localhost](http://localhost) in your browser (80 is the
default port). This time it is a fully functional website which could actually
be used in production.

## 9. Final configuration.
### Add boards
Follow the configuration guide available in the same directory as this file.
A few steps were already done previously. I recommend reading the entire file
now and performing steps like creating user accounts and boards.

### Test
Run:

    $ cd /var/www/archive_chan/archive_chan_flask
    $ sudo su python-server
    $ source ../archive_chan_virtualenv/bin/activate
    (archive_chan_virtualenv) $ export ARCHIVE_CHAN_SETTINGS=/var/www/archive_chan/settings.py
    (archive_chan_virtualenv) $ python run.py update --progress

You can actually wait for it to finish. You should notice new threads appearing
one by one on the website. If the command quickly finished without any output
you forgot to create the boards.

### Set up cron
We want the archive to automatically update periodically. Create two scripts.

`/var/www/archive_chan/update` to download new threads:

    #!/bin/bash
    cd /var/www/archive_chan/archive_chan_flask
    source ../archive_chan_virtualenv/bin/activate
    ARCHIVE_CHAN_SETTINGS="/var/www/archive_chan/settings.py" python run.py update

`/var/www/archive_chan/remove` to remove old threads:

    #!/bin/bash
    cd /var/www/archive_chan/archive_chan_flask
    source ../archive_chan_virtualenv/bin/activate
    ARCHIVE_CHAN_SETTINGS="/var/www/archive_chan/settings.py" python run.py remove_old_threads

Set the owner of those scripts to `python-server` with `chown` and add the
execution permission with `chmod`.

Set up cron to run them periodically by adding this to your `/etc/crontab`:

    */10 * * * * python-server /var/www/archive_chan/update
    5 */2 * * * python-server /var/www/archive_chan/remove

First command will run every 10 minutes and the second one every 2 hours.

[nginx]: http://nginx.com/
[gunicorn]: http://gunicorn.org
[supervisor]: http://supervisord.org/
[virtualenv]: https://virtualenv.pypa.io/en/latest/
[postgresql]: http://www.postgresql.org/

[pip_installation]: https://pip.pypa.io/en/latest/installing.html
[virtualenv_installation]: http://virtualenv.readthedocs.org/en/latest/virtualenv.html#installation
[virtualenv_docs]: http://virtualenv.readthedocs.org/en/latest/virtualenv.html#usage
[postgresql_guide]: https://wiki.debian.org/PostgreSql
[postgresql_guide_user]:https://wiki.debian.org/PostgreSql#User_access
[user_creation_guide]: http://www.debian-administration.org/article/2/Adding_new_users
