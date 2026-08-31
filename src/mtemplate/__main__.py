#!/usr/bin/env python3
import argparse
import json

from pathlib import Path

from mtemplate.core import MTemplate


# parser #

parser = argparse.ArgumentParser(prog='mtemplate', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('command', choices=['render'], help='command to run')
parser.add_argument('--source', '-s', type=Path, default=None, help='source file to render (if command is "render")')
parser.add_argument('--output', type=Path, default=None, help='output file for rendering')
parser.add_argument('--vars', type=str, default=None, help='JSON string of variables to pass to the template')

args = parser.parse_args()


# run program #

if args.command == 'render':
    extractor = MTemplate(args.source)

    template_vars = dict() if args.vars is None else json.loads(args.vars)

    extractor.parse()
    rendered_template = extractor.render_template(template_vars)

    if args.output is None:
        print(rendered_template)

else:
    parser.print_help()
