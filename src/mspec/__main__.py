import argparse
import os
import shutil
import json
from pathlib import Path
from mspec.core import *
from mspec.lingo import lingo_app, lingo_execute, render_output

#
# argument parser
#

description = '''mspec command line interface, run "mspec <command> --help" for more information on a command.'''
parser = argparse.ArgumentParser(description=description, prog='mspec')
subparsers = parser.add_subparsers(dest='command', help='Available commands')

# specs command #

specs_parser = subparsers.add_parser(
    'specs',
    help='List all built-in spec files'
)

specs_parser.add_argument(
    '--json',
    action='store_true',
    help='Output specs in JSON format'
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

example_parser.add_argument(
    '--yes',
    '-y',
    action='store_true',
    help='Automatically answer yes to overwrite prompts'
)
example_parser.add_argument(
    '--no',
    '-n',
    action='store_true',
    help='Automatically answer no to overwrite prompts'
)
example_parser.add_argument(
    '--display',
    '-d',
    action='store_true',
    help='Display the result of the example spec instead of writing to file'
)
example_parser.add_argument(
    '--init',
    action='store_true',
    help='If displaying, initialize the spec before displaying'
)

# examples command #

examples_parser = subparsers.add_parser(
    'examples',
    help='Copy all built-in specs to the current directory'
)
examples_parser.add_argument(
    '--output-dir',
    '-o',
    type=str,
    default='.',
    help='Output directory to copy all built-in specs to (default: current directory)'
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
run_parser.add_argument(
    '--params',
    '-p',
    type=str,
    help='JSON string of parameters for the run spec'
)

# execute command #

execute_parser = subparsers.add_parser(
    'execute',
    help='Execute a lingo script spec and print the result'
)
execute_parser.add_argument(
    'spec',
    type=str,
    help='Lingo script spec file path (.json) or built-in spec name'
)
execute_parser.add_argument(
    '--params',
    '-p',
    type=str,
    help='JSON string of parameters for the execute spec'
)

#
# run commands
#

args = parser.parse_args()

if not args.command:
    parser.print_help()
    raise SystemExit(1)

if args.command == 'specs':
    specs = builtin_spec_files()

    if args.json:
        print(json.dumps(specs, indent=4))

    else:
        print('Builtin browser2 spec files:')
        for spec in specs['browser2']:
            print(f' - {spec}')

        print('Builtin generator spec files:')
        for spec in specs['generator']:
            print(f' - {spec}')

        print('Builtin mspec lingo script spec files:')
        for spec in specs['lingo_script']:
            print(f' - {spec}')

        print('Builtin mspec lingo script test data spec files:')
        for spec in specs['lingo_script_test_data']:
            print(f' - {spec}')

elif args.command == 'example':

    directories = [
        SAMPLE_BROWSER2_SPEC_DIR,
        SAMPLE_GENERATOR_SPEC_DIR,
        SAMPLE_LINGO_SCRIPT_SPEC_DIR
    ]

    for directory in directories:
        spec_path: Path = directory / args.spec
        if spec_path.exists():
            output_path = Path.cwd() / args.spec
            if args.display:
                if args.init:
                    display = load_generator_spec(spec_path, try_examples=False)
                    print(json.dumps(display, indent=4))

                else:
                    with open(spec_path, 'r') as f:
                        print(f.read())

            else:
                if output_path.exists():
                    if args.yes:
                        pass
                    elif args.no:
                        print(f'File already exists, not overwriting: {args.spec}')
                        raise SystemExit(0)
                    else:
                        response = input(f'File {output_path.name} exists, overwrite {args.spec}? (y/n): ')
                        if response.lower() != 'y':
                            print('Aborting copy.')
                            raise SystemExit(1)
                        
                shutil.copy(spec_path, output_path)
                print(f'Copied example spec file to current directory: {args.spec}')

            break
    else:
        print(f'Example spec file not found: {spec_path}')
        raise SystemExit(1)

elif args.command == 'examples':
    shutil.copytree(SAMPLE_DATA_DIR, args.output_dir, dirs_exist_ok=True)

elif args.command == 'run':
    spec = load_browser2_spec(args.spec, display=True)
    params = json.loads(args.params) if args.params else {}
    app = lingo_app(spec, **params)
    doc = render_output(app)
    print(json.dumps(doc, indent=4, sort_keys=True))

elif args.command == 'execute':
    lingo_script = load_lingo_script_spec(args.spec)
    params = json.loads(args.params) if args.params else {}
    app = lingo_app(lingo_script, **params)
    result = lingo_execute(app, lingo_script['output'])
    print(json.dumps(result, indent=4, sort_keys=True))

else:
    print('Unknown command')
    raise SystemExit(1)