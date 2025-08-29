#!/usr/bin/env python3
from mspec import load_spec
from mtemplate.browser1 import MTemplateBrowser1Project
from mtemplate.py import MTemplatePyProject
import argparse
from pathlib import Path

# parser #

parser = argparse.ArgumentParser(description='mtemplate - cli')
parser.add_argument('command', choices=['render', 'cache'], help='Use "render" to generate an app from a spec file, "cache" to cache jinja2 templates')
parser.add_argument('--spec', type=str, default='test-gen.yaml', help='spec file to use, first attempt to use <spec> if it exists, else try <spec> in the built in template repo')
parser.add_argument('--env-file', type=str, default=None, help='path to .env file to copy to output dir for python app (if rendering python app)')
parser.add_argument('--app', type=str, default='both', choices=['py', 'browser1', 'both'], help='Which apps to apply command to, choices are "py", "browser1" or "both", default: "both"')
parser.add_argument('--output', type=Path, default=None, help='output directory for rendering')
parser.add_argument('--debug', action='store_true', help='write jinja template files for debugging, and do not erase output dir before rendering')
parser.add_argument('--disable-strict', action='store_true', help='disable jinja strict mode when rendering - discouraged but may be useful for debugging')
parser.add_argument('--use-cache', action='store_true', default=True, help='use cached templates if available (default: True)')
parser.add_argument('--no-cache', action='store_true', help='do not use cached templates, extract fresh templates')

args = parser.parse_args()

# Determine use_cache value
use_cache = args.use_cache and not args.no_cache

# run program #

if args.command == 'cache':
    if args.app in ['both', 'py']:
        MTemplatePyProject.build_cache(load_spec(args.spec))
        
    if args.app in ['both', 'browser1']:
        MTemplateBrowser1Project.build_cache(load_spec(args.spec))

elif args.command == 'render':
    if args.app in ['both', 'py']:
        py_out = None if args.output is None else args.output / 'py'
        MTemplatePyProject.render(load_spec(args.spec), args.env_file, py_out, args.debug, args.disable_strict, use_cache)

    if args.app in ['both', 'browser1']:
        browser1_out = None if args.output is None else args.output / 'browser1'
        MTemplateBrowser1Project.render(load_spec(args.spec), args.env_file, browser1_out, args.debug, args.disable_strict, use_cache)

else:
    parser.print_help()
