from inspect import isclass
from flask.ext.script import Manager, Command
from archive_chan import create_app, commands


commands = [
    'create_user', 'update', 'remove_orphaned_files', 'remove_old_threads',
    'recount_denormalized', 'sql', 'init_db'
]


def add_commands(names, manager):
    pack = __import__('archive_chan.commands', fromlist=names)
    for name in commands:
        mod = getattr(pack, name)
        command = getattr(mod, 'Command')
        manager.add_command(name, command)


app = create_app()
manager = Manager(app)
add_commands(commands, manager)


if __name__ == "__main__":
    manager.run()
