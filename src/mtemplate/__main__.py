#!/usr/bin/env python3
import json
import argparse

from pathlib import Path

from mtemplate.core import MTemplateExtractor, apply_template_slots

# parser #

parser = argparse.ArgumentParser(prog='mtemplate', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('command', choices=['render', 'slots'], help='command to run')
parser.add_argument('--source', '-s', type=Path, default=None, help='source directory for templates')
parser.add_argument('--debug', action='store_true', help='debug jinja template, if no --output provided it will be printed to screen, otherwise it will be written to <output>.jinja2')
parser.add_argument('--disable-strict', action='store_true', help='disable strict mode for jinja template rendering, not recommended for general use, only debugging')
parser.add_argument('--template', '-t', type=str, default=None, help='template file to render')
parser.add_argument('--output', '-o', type=Path, default=None, help='output file for rendering')
parser.add_argument('--vars', type=str, default=None, help='JSON string of variables to pass to the template')

args = parser.parse_args()

# run program #

if args.command == 'render':
    template_vars = dict() if args.vars is None else json.loads(args.vars)

    if args.source is None:
        raise ValueError('Must provide --source with "render" command')
    
    extractor = MTemplateExtractor.init_from_dir(args.source, debug=args.debug, disable_strict=args.disable_strict)
    rendered_template = extractor.render_template(args.template, template_vars, output=args.output)

    if args.output is None:
        print(rendered_template)

elif args.command == 'slots':
    if args.source is None:
        raise ValueError('Must provide --source with "slots" command')
                            
    rendered_child = apply_template_slots(args.source, args.output)

    if args.output is None:
        print(rendered_child)

else:
    parser.print_help()
