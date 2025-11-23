#!/usr/bin/env python3
from mspec.core import load_generator_spec
from mtemplate.test import test_spec
from mtemplate import setup_generated_app, run_server_and_app_tests
from mtemplate.browser1 import MTemplateBrowser1Project
from mtemplate.py import MTemplatePyProject
from mtemplate.bootstrap import MappBootstrapProject

import argparse

from pathlib import Path

# parser #

description = """mtemplate  -  Medium Tech Template App Generator CLI\n
Available commands:
    render:    generate an app from a spec file
    cache:     cache jinja2 templates
    setup:     setup a generated app
    test:      run generated app tests for generated py/browser1 apps
    test-spec: test a generated app from a spec file
    slots:     apply template slots to child templates."""

parser = argparse.ArgumentParser(description=description, prog='mtemplate', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('command', choices=['render', 'cache', 'setup', 'test', 'test-spec', 'slots'], help='command to run')
parser.add_argument('--spec', type=str, default='test-gen.yaml', help='spec file to use, first attempt to use <spec> if it exists, else try <spec> in the built in template repo')
parser.add_argument('--env-file', type=str, default=None, help='path to .env file to copy to output dir for python app (if rendering python app)')
parser.add_argument('--app', type=str, default='both', choices=['py', 'browser1', 'both', 'bootstrap'], help='Which apps to apply command to, choices are "py", "browser1" or "both", default: "both"')
parser.add_argument('--source-dir', type=Path, default=None, help='source directory of generated app to setup or test (if command is "setup" or "test")')
parser.add_argument('--output', type=Path, default=None, help='output directory for rendering')
parser.add_argument('--debug', action='store_true', help='write jinja template files for debugging, and do not erase output dir before rendering')
parser.add_argument('--disable-strict', action='store_true', help='disable jinja strict mode when rendering - discouraged but may be useful for debugging')
parser.add_argument('--use-cache', action='store_true', default=True, help='use cached templates if available (default: True)')
parser.add_argument('--no-cache', action='store_true', help='do not use cached templates, extract fresh templates')
parser.add_argument('--cmd', type=str, nargs='*', default=None, help='CLI command for template app (used with "test-spec" command)')
parser.add_argument('--host', type=str, default=None, help='host for http client in "test-spec" command (if host diff than in spec file)')

args = parser.parse_args()

# Determine use_cache value
use_cache = args.use_cache and not args.no_cache

# run program #

if args.command == 'cache':
    if args.app in ['both', 'py']:
        MTemplatePyProject.build_cache(load_generator_spec(args.spec))
        
    if args.app in ['both', 'browser1', 'bootstrap']:
        MTemplateBrowser1Project.build_cache(load_generator_spec(args.spec))
        
    if args.app == 'bootstrap':
        MappBootstrapProject.build_cache(load_generator_spec(args.spec))

elif args.command == 'render':
    if args.app in ['both', 'py']:
        py_out = None if args.output is None else args.output / 'py'
        MTemplatePyProject.render(load_generator_spec(args.spec), args.env_file, py_out, args.debug, args.disable_strict, use_cache)

    if args.app in ['both', 'browser1', 'bootstrap']:
        browser1_out = None if args.output is None else args.output / 'browser1'
        MTemplateBrowser1Project.render(load_generator_spec(args.spec), args.env_file, browser1_out, args.debug, args.disable_strict, use_cache)
    
    if args.app == 'bootstrap':
        bootstrap_out = None if args.output is None else args.output / 'bootstrap'
        MappBootstrapProject.render(args.spec, load_generator_spec(args.spec), args.env_file, bootstrap_out, args.debug, args.disable_strict, use_cache)

elif args.command == 'setup':
    if args.source_dir is None:
        print('Error: --source-dir is required for setup command')
    else:
        setup_generated_app(args.source_dir)

elif args.command == 'test':
    if args.source_dir is None:
        print('Error: --source-dir is required for test command')
    else:
        run_server_and_app_tests(args.source_dir)

elif args.command == 'test-spec':
    result = test_spec(args.spec, args.cmd, args.host)
    if not result:
        raise SystemExit(1)

elif args.command == 'slots':
    if args.app in ['both', 'py']:
        MTemplatePyProject.apply_slots_to_children(debug=args.debug)

    if args.app in ['both', 'browser1']:
        MTemplateBrowser1Project.apply_slots_to_children(debug=args.debug)

else:
    parser.print_help()
