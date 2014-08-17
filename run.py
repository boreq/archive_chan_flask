from flask.ext.script import Manager
from archive_chan import app


manager = Manager(app)


from archive_chan.commands import update, remove_old_threads, remove_orphaned_files
manager.add_command('update', update.Command)
manager.add_command('remove_old_threads', remove_old_threads.Command)
manager.add_command('remove_orphaned_files', remove_orphaned_files.Command)


if __name__ == "__main__":
    manager.run()
