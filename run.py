from flask.ext.script import Manager
from archive_chan import create_app


app = create_app()
manager = Manager(app)


from archive_chan.commands import update, remove_old_threads, remove_orphaned_files
from archive_chan.commands import remove_old_threads
from archive_chan.commands import remove_orphaned_files
from archive_chan.commands import recount_denormalized
manager.add_command('update', update.Command)
manager.add_command('remove_old_threads', remove_old_threads.Command)
manager.add_command('remove_orphaned_files', remove_orphaned_files.Command)
manager.add_command('recount_denormalized', recount_denormalized.Command)


if __name__ == "__main__":
    manager.run()
