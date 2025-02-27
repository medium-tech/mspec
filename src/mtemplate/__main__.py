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
parser.add_argument('command', choices=['extract', 'render-py', 'render-html'], help='command to run')
parser.add_argument('--spec', type=str, default='test-gen.yaml', help='spec file pattern')
parser.add_argument('--source', type=Path, default=None, help='source to extract template from')
parser.add_argument('--output', type=Path, default=None, help='output directory')
parser.add_argument('--debug', action='store_true', help='print debug output')
parser.add_argument('--disable-strict', action='store_true', help='disable jinja strict mode - discouraged but can be used for debugging')

args = parser.parse_args()

# run program #

if args.command == 'extract':
    template = MTemplateExtractor.template_from_file(args.source)
        
    if args.output is None:
        print(template.create_template())
    else:
        with open(args.output, 'w+') as f:
            f.write(template.create_template())

elif args.command == 'render-py':
    MTemplatePyProject.render(load_spec(args.spec), args.output, args.debug, args.disable_strict)

elif args.command == 'render-html':
    MTemplateHTMLProject.render(load_spec(args.spec), args.output, args.debug, args.disable_strict)
