#!/usr/bin/env python3
from mspec import load_spec
from mtemplate import MTemplateExtractor
from mtemplate.html import render_html_templates
from mtemplate.py import render_py_templates
import argparse
from pathlib import Path

# parser #

parser = argparse.ArgumentParser(description='mtemplate - cli')
parser.add_argument('command', choices=['extract', 'render-py', 'render-html'], help='command to run')
parser.add_argument('--spec', type=str, default='*.yaml', help='spec file pattern')
parser.add_argument('--source', type=Path, default=None, help='source to extract template from')
parser.add_argument('--output', type=Path, default=None, help='output directory')
parser.add_argument('--debug', action='store_true', help='print debug output')

args = parser.parse_args()

# run program #

if args.command == 'extract':
    template = MTemplateExtractor.template_from_file(args.source)
    if args.output is None:
        print(template)
    else:
        with open(args.output, 'w+') as f:
            f.write(template)

elif args.command == 'render-py':
    render_py_templates(load_spec(args.spec), args.output, args.debug)

elif args.command == 'render-html':
    render_html_templates(load_spec(args.spec), args.output, args.debug)
