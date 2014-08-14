from flask.ext.script import Manager
from archive_chan import app


manager = Manager(app)


from archive_chan.commands import test
from archive_chan.commands import update
manager.add_command('test', test.Command)
manager.add_command('update', update.Command)


if __name__ == "__main__":
    manager.run()
