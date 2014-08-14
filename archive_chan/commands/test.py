from flask.ext import script

class Command(script.Command):
    def run(self):
        print('hello world')
