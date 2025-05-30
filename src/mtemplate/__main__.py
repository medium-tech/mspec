#!/usr/bin/env python3
from mspec import load_spec
from mtemplate import MTemplateExtractor
from mtemplate.html import MTemplateHTMLProject
from mtemplate.py import MTemplatePyProject
import argparse
from pathlib import Path
import json

# parser #

parser = argparse.ArgumentParser(description='mtemplate - cli')
parser.add_argument('command', choices=['extract', 'render', 'render-py', 'render-html'], help='"extract" a template from a file, "render" a template from a spec file, or only render the python or html template with "render-py" or "render-html"')
parser.add_argument('--spec', type=str, default='test-gen.yaml', help='spec file pattern')
parser.add_argument('--source', type=Path, default=None, help='source file to extract template from')
parser.add_argument('--output', type=Path, default=None, help='output directory for rendering or out file for extraction')
parser.add_argument('--debug', action='store_true', help='write jinja template files for debugging, and do not erase output dir before rendering')
parser.add_argument('--disable-strict', action='store_true', help='disable jinja strict mode when rendering - discouraged but may be useful for debugging')

args = parser.parse_args()

# run program #

if args.command == 'extract':
    template = MTemplateExtractor.template_from_file(args.source)
        
    if args.output is None:
        print(template.create_template())
    else:
        with open(args.output, 'w+') as f:
            f.write(template.create_template())

if args.command in ['render', 'render-py']:
    MTemplatePyProject.render(load_spec(args.spec), args.output, args.debug, args.disable_strict)

if args.command in ['render', 'render-html']:
    MTemplateHTMLProject.render(load_spec(args.spec), args.output, args.debug, args.disable_strict)
