import argparse
import shutil
import json
from pathlib import Path
from mspec import *
from mspec.markup import lingo_app, render_output, lingo_update_state

#
# argument parser
#

parser = argparse.ArgumentParser(description='MSpec command line interface')
subparsers = parser.add_subparsers(dest='command', help='Available commands')

# specs command #

specs_parser = subparsers.add_parser(
    'specs',
    help='List all built-in spec files'
)

# example command #

example_parser = subparsers.add_parser(
    'example',
    help='Copy a built-in spec to the current directory'
)
example_parser.add_argument(
    'spec',
    type=str,
    help='Built-in spec name to copy to current directory'
)

# run command #

run_parser = subparsers.add_parser(
    'run',
    help='Execute a browser2 spec and print the result'
)
run_parser.add_argument(
    'spec',
    type=str,
    help='Browser2 spec file path (.json) or built-in spec name'
)

args = parser.parse_args()

#
# run commands
#

if not args.command:
    parser.print_help()
    raise SystemExit(1)

if args.command == 'specs':
    specs = builtin_spec_files()

    print('Builtin browser2 spec files:')
    for spec in specs['browser2_specs']:
        print(f' - {spec}')

    print('Builtin generator spec files:')
    for spec in specs['generator_specs']:
        print(f' - {spec}')

    print('Builtin mspec lingo script spec files:')
    for spec in specs['lingo_script_specs']:
        print(f' - {spec}')

elif args.command == 'example':

    directories = [
        sample_browser2_spec_dir,
        sample_generator_spec_dir,
        sample_lingo_script_spec_dir
    ]

    for directory in directories:
        spec_path: Path = directory / args.spec
        if spec_path.exists():
            shutil.copy(spec_path, Path.cwd() / args.spec)
            print(f'Copied example spec file to current directory: {args.spec}')
            break
    else:
        print(f'Example spec file not found: {spec_path}')
        raise SystemExit(1)

elif args.command == 'run':
    print(f'Running run command with spec: {args.spec}')
    if not args.spec.endswith('.json'):
        print('Spec file must be a .json file for run command')
        raise SystemExit(1)
    spec = load_browser2_spec(args.spec)
    app = lingo_app(spec)
    doc = render_output(lingo_update_state(app))
    print(json.dumps(doc, indent=4))

else:
    print('Unknown command')
    raise SystemExit(1)