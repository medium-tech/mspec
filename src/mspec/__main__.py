import argparse
from mspec import spec
from mspec.html_gen import render_html
from mspec.py_gen import render_py
from pprint import pprint

parser = argparse.ArgumentParser(description='MSpec command line interface')
parser.add_argument('command', choices=['spec', 'render', 'html', 'py'],  help='command to run')

args = parser.parse_args()
match args.command:
    case 'spec':
        pprint(spec())

    case 'render':
        render_html()
        render_py()

    case 'html':
        render_html()
    
    case 'py':
        render_py()

    case _:
        print('Unknown command')
        raise SystemExit(1)
