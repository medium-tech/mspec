#!/usr/bin/env python3
from mspec import load_spec
from mtemplate import MTemplateExtractor
from mtemplate.browser1 import MTemplateBrowser1Project
from mtemplate.py import MTemplatePyProject
import argparse
from pathlib import Path

# parser #

parser = argparse.ArgumentParser(description='mtemplate - cli')
parser.add_argument('command', choices=['tree-py', 'tree-browser1', 'extract', 'render', 'render-py', 'render-browser1'], help='display "tree" of app templates, "extract" a template from a file, "render" a template from a spec file, or only render the python or browser1 template with "render-py" or "render-browser1"')
parser.add_argument('--spec', type=str, default='test-gen.yaml', help='spec file pattern')
parser.add_argument('--source', type=Path, default=None, help='source file to extract template from')
parser.add_argument('--output', type=Path, default=None, help='output directory for rendering or out file for extraction')
parser.add_argument('--debug', action='store_true', help='write jinja template files for debugging, and do not erase output dir before rendering')
parser.add_argument('--disable-strict', action='store_true', help='disable jinja strict mode when rendering - discouraged but may be useful for debugging')

args = parser.parse_args()

# run program #

if args.command == 'tree-py':
    MTemplatePyProject.tree(load_spec(args.spec))

elif args.command == 'tree-browser1':
    MTemplateBrowser1Project.tree(load_spec(args.spec))

elif args.command == 'extract':
    template = MTemplateExtractor.template_from_file(args.source)
        
    if args.output is None:
        print(template.create_template())
    else:
        with open(args.output, 'w+') as f:
            f.write(template.create_template())

elif args.command == 'render':
    MTemplatePyProject.render(load_spec(args.spec), args.output / 'py', args.debug, args.disable_strict)
    MTemplateBrowser1Project.render(load_spec(args.spec), args.output / 'browser1', args.debug, args.disable_strict)

elif args.command == 'render-py':
    MTemplatePyProject.render(load_spec(args.spec), args.output, args.debug, args.disable_strict)

elif args.command == 'render-browser1':
    MTemplateBrowser1Project.render(load_spec(args.spec), args.output, args.debug, args.disable_strict)
else:
    parser.print_help()
