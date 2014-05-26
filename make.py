#!/usr/bin/env python
import os

js_concat = [
    [
        [
            'lib/jquery.timeago.js',
            'lib/highlight.pack.js',
            'lib/jquery.qtip.js',
            'lib/jquery.cookie.js',
            'lib/jquery.dotdotdot.min.js',
            'lib/jquery.autocomplete.js',
            'manipulate_height.js',
            'parse.js',
            'ajax.js',
            'init.js',
        ],
        'main.js'
    ],
    [
        [
            'board_stats_draw.js',
        ],
        'board_stats.js'
    ]
] 

css_concat = [
    [
        [
            'import.css',
            'reset.css',
            'style.scss',
            'highlight.css',
            'jquery.qtip.css',
        ],
        'main.css'
    ]
]


current_directory = os.path.dirname(os.path.realpath(__file__))

path = os.path.join(current_directory, "archive_chan/static/archive_chan")
js_path = os.path.join(path, 'js')
css_path = os.path.join(path, 'css')


def get_cat_list(paths):
    files = []
    for path in paths:
        if is_sass(path):
            files.append(insert_min_extension(replace_extension(path, '.css')))
        else:
            files.append(insert_min_extension(path))
    return files
        
def insert_min_extension(path):
    return os.path.join(os.path.splitext(path)[0] + '.min' + os.path.splitext(path)[1])

def replace_extension(path, new):
    return os.path.join(os.path.splitext(path)[0] + new)

def is_sass(path):
    return (os.path.splitext(path)[1] ==  '.scss')

def handle(files_list, files_directory, out_file):
    files_list = [os.path.join(files_directory, path) for path in files_list]

    # SASS.
    for path in files_list:
        if is_sass(path):
            os.system(format("sass %s %s" % (path, replace_extension(path, '.css'))))

    # Minify.
    for path in files_list:
        if is_sass(path):
            out_min_file = insert_min_extension(replace_extension(path, '.css'))
            in_file = replace_extension(path, '.css')
        else:
            out_min_file = insert_min_extension(path)
            in_file = path

        print('Minifty: %s' % in_file)
        os.system(format("yui-compressor -o %s %s" % (out_min_file, in_file)))

    # Concat.
    os.system(format("cat %s > %s" % (" ".join(get_cat_list(files_list)), os.path.join(files_directory, out_file))))

    # Remove minified temp files.
    for path in files_list:

        if is_sass(path):
            out_file = insert_min_extension(replace_extension(path, '.css'))
            in_file = replace_extension(path, '.css')
            os.remove(in_file)
        else:
            out_file = insert_min_extension(path)

        os.remove(out_file)


for obj in js_concat:
    handle(obj[0], js_path, obj[1])

for obj in css_concat:
    handle(obj[0], css_path, obj[1])
