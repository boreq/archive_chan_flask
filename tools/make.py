#!/usr/bin/env python
import argparse
import json
import logging
import os
import sys


def replace_extension(path, in_ext, out_ext):
    """Replaces an extension.

    path: path in which the extension will change
    in_ext: input extension.
    out_ext: output extension.
    """
    return path[:-len(in_ext)] + out_ext


class ToolData(object):
    """Stores the name of the conversion program and extensions of the input and
    output file.
    """

    def __init__(self, chain_element, next_chain_element):
        self.tool = chain_element['tool']
        self.input_ext = chain_element['extension']
        self.output_ext = None
        if next_chain_element is not None:
            self.output_ext = next_chain_element['extension']


class Conversion(object):
    """Stores paths of the input and output files and tool used for conversion.

    input_path: path to the input file.
    output_path: path to the output file created by this conversion.
    tool_data: tool used to convert the file. ToolData object.
    """

    def __init__(self, input_path, output_path, tool_data):
        self.input_path = input_path
        self.output_path = output_path
        self.tool_data = tool_data

    @property
    def command(self):
        return self.tool_data.tool % (
            self.input_path,
            self.output_path
        )


class Task(object):
    """Task defined in the makefile."""
    def __init__(self, input_files, output_file):
        self.input_files = input_files
        self.output_file = output_file


class Makefile(object):
    """Provides ways to query a makefile."""

    def __init__(self, makefile=None):
        if makefile is not None:
            self.load(makefile)

    def _get_full_path(self, relative_path):
        """Converts relative path defined in the makefile to absolute path."""
        absolute_path = os.path.join(self.makefile_dir, self.makefile_data['path'],
                                     relative_path)
        return os.path.abspath(absolute_path)

    def load(self, makefile):
        """Loads a makefile.

        makefile: path to a makefile.
        """
        with open(makefile, 'r') as f:
            self.makefile_data = json.load(f)

        self.makefile_path = makefile
        self.makefile_dir = os.path.dirname(makefile)

        # Convert all relative path to absolute paths.
        for task in self.makefile_data['tasks']:
            task['input'] = [self._get_full_path(path) for path in task['input']]
            task['output'] = self._get_full_path(task['output'])

    def find_tool(self, input_path):
        """Finds a tool used for conversion. Returns ToolData.

        input_path: path to a converted file. It will be used to get file
                    extension.
        """
        next_chain_element = None
        for chain in self.makefile_data['chains']:
            for chain_element in reversed(chain):
                if input_path.endswith(chain_element['extension']):
                    return ToolData(chain_element, next_chain_element)
                next_chain_element = chain_element
        return None

    def get_conversion_chain(self, input_path):
        """Get all conversion steps for the given file (list of Conversion
        objects).
        """
        chain = []
        while True:
            tool_data = self.find_tool(input_path)
            if tool_data.tool is None:
                break
            output_path = replace_extension(input_path, tool_data.input_ext, tool_data.output_ext)
            chain.append(Conversion(input_path, output_path, tool_data))
            input_path = output_path
        return chain

    def task_generator(self):
        for task in self.makefile_data['tasks']:
            yield Task(task['input'], task['output'])


class Make(object):
    """Executes task defined in the Makefile.

    makefile: Makefile object.
    """

    def __init__(self, makefile, dry_run=False):
        self.makefile = makefile
        self.dry_run = dry_run

    def stdout(self, text):
        """Writes to stdout."""
        sys.stdout.write(text)
        sys.stdout.flush()

    def execute(self, command):
        """Executes a command."""
        logging.debug(command)
        if not self.dry_run:
            if os.system(command) != 0:
                raise Exception('Could not execute command:\n%s' % command)

    def concat(self, file_list, output_path):
        self.stdout(' > ')
        command = 'cat %s > %s' % (' '.join(file_list), output_path)
        self.execute(command)

    def remove_files(self, file_list):
        for file_path in file_list:
            self.stdout('-')
            logging.debug('Remove %s', file_path)
            if not self.dry_run:
                os.remove(file_path)

    def convert_file(self, input_path):
        """Converts the file using defined conversion chains. Returns its final
        path.
        """
        conversion_chain = self.makefile.get_conversion_chain(input_path)
        if len(conversion_chain) == 0:
            return input_path

        for conversion in conversion_chain:
            self.stdout('*')
            self.execute(conversion.command)

        return conversion_chain[-1].output_path

    def get_intermediate_files(self, file_path):
        """Get the list intemediate files created during conversion."""
        return [conversion.output_path \
            for conversion in self.makefile.get_conversion_chain(file_path)]

    def run(self, task):
        """Process files, concat them and delete intermidiate files."""
        final_paths = []
        for input_path in task.input_files:
            final_path = self.convert_file(input_path)
            final_paths.append(final_path)

        self.concat(final_paths, task.output_file)

        for input_path in task.input_files:
            self.remove_files(self.get_intermediate_files(input_path))

    def all(self):
        """Run all tasks defined in the makefile."""
        for task in self.makefile.task_generator():
            self.run(task)
            self.stdout('\n')


if __name__ == '__main__':
    # Parse the arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--makefile', default='makefile.json',
                        help='Relative path to a makefile.')
    parser.add_argument('--verbosity', default='warning',
                        choices=['critical', 'error', 'warning', 'info', 'debug'])
    parser.add_argument('--dryrun', action='store_true')
    args = parser.parse_args()

    # Configure logging.
    numeric_level = getattr(logging, args.verbosity.upper(), None)
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=numeric_level)

    makefile = Makefile(args.makefile)
    make = Make(makefile, dry_run=args.dryrun)
    make.all()
