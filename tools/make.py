#!/usr/bin/env python
import os, argparse, json, sys

colors = {
    'white': '\033[0m',
    'red': '\033[31m',
    'green': '\033[32m',
    'orange': '\033[33m',
    'blue': '\033[34m',
    'violet': '\033[35m',
}

def color(color, text):
    return format('%s%s%s' % (colors[color], text, colors['white']))

# Parse the arguments.
parser = argparse.ArgumentParser()
parser.add_argument('-m', '--makefile', help='Path to a makefile relative to the current working directory.', default='makefile.json')
parser.add_argument('--dryrun', help='Don\'t execute any commands.', action='store_true')
parser.add_argument('--verbose', help='Increase verbosity', action='store_true')
args = parser.parse_args()

# Establish the path to the makefile and its directory.
makefile_path = os.path.join(os.getcwd(), args.makefile)
makefile_dir = os.path.dirname(makefile_path)

if args.verbose:
    print(args)
    print('Makefile path: %s' % makefile_path)
    print('Makefile dir: %s' % makefile_dir)

# Load json data.
makefile=open(makefile_path)
makefile_data = json.load(makefile)
makefile.close()

def replace_extension(file_path, current_ext, future_ext):
    return file_path[:-len(current_ext)] + future_ext

def get_full_path(file_path):
    return os.path.abspath(os.path.join(makefile_dir, makefile_data['path'], file_path))

def find_tool(file_path):
    output_extension = None

    for chain in makefile_data['chains']:
        for chain_element in reversed(chain):
            if file_path.endswith(chain_element['extension']):
                return (chain_element['tool'], chain_element['extension'], output_extension)

            output_extension = chain_element['extension']

    return None

def get_conversion_chain(file_path):
    chain = []

    while True:
        tool, current_extension, output_extension = find_tool(file_path)

        if tool is None:
            break
        else:
            output_file_path = replace_extension(file_path, current_extension, output_extension)
            chain.append((file_path, output_file_path, tool))
            file_path = output_file_path

    return chain

def process_file(file_path):
    if args.verbose:
        print('\nPROCESS: %s' % (file_path))

    conversion_chain = get_conversion_chain(file_path)

    for conversion in conversion_chain:
        if args.verbose:
            print('  CONVERT %s TO %s WITH %s' % conversion)
        else:
            print(color('green', '*'), end='', flush=True)

        command = format(conversion[2] % (get_full_path(conversion[0]), get_full_path(conversion[1])))
        if args.verbose:
            print(command)
        if not args.dryrun:
            if os.system(command) != 0:
                sys.exit(1)

    if len(conversion_chain) > 0:
        return conversion_chain[-1][1]
    else:
        return file_path

def get_intermediate_files(file_path):
    return [conversion[1] for conversion in get_conversion_chain(file_path)]

def handle(task):
    final_files = []

    # Process files.
    for file_path in task['input']:
        final_files.append(process_file(file_path))
    
    final_files = [get_full_path(file_path) for file_path in final_files]

    # Concat final files.
    if args.verbose:
        print('\nCONCAT\n')
    else:
        print(color('violet', ' > '), end='', flush=True)

    command = format("cat %s > %s" % (" ".join(final_files), get_full_path(task['output'])))
    if args.verbose:
        print(command)
    if not args.dryrun:
        if os.system(command) != 0:
            sys.exit(1)

    # Remove intermediate files.
    for file_path in task['input']:
        for intermediate_file in get_intermediate_files(file_path):
            if args.verbose:
                print('REMOVE: %s' % intermediate_file)
            else:
                print(color('red', '-'), end='', flush=True)

            remove_path = get_full_path(intermediate_file)
            if args.verbose:
                print(remove_path)
            if not args.dryrun:
                try:
                    os.remove(remove_path)
                except:
                    pass

for task in makefile_data['tasks']:
    handle(task)
    print('')
