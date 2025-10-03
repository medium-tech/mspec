import argparse
import shutil
import json
from mspec import load_spec, sample_spec_dir, builtin_spec_files, load_browser2_spec
from mspec.markup import lingo_app, render_output, lingo_update_state

#
# argument parser
#

parser = argparse.ArgumentParser(description='MSpec command line interface')
subparsers = parser.add_subparsers(dest='command', help='Available commands')


# show command #

show_parser = subparsers.add_parser(
    'show', 
    help='Load and display a spec file'
)
show_parser.add_argument(
    'spec',
    type=str,
    help='Spec file path or built-in spec name. The app first tries to load from the file system, then falls back to built-in specs.'
)

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

if args.command == 'show':
    if args.spec.endswith('.json'):
        print(json.dumps(load_browser2_spec(args.spec), indent=4))
    else:
        print(json.dumps(load_spec(args.spec), indent=4))

elif args.command == 'specs':
    specs = builtin_spec_files()

    print('Builtin browser2 spec files:')
    for spec in specs:
        if spec.endswith('json'):
            print(f' - {spec}')

    print('Builtin mspec template app spec files:')
    for spec in specs:
        if spec.endswith('yaml') or spec.endswith('yml'):
            print(f' - {spec}')

elif args.command == 'example':
    spec_path = sample_spec_dir / args.spec
    
    if not spec_path.exists():
        print(f'Example spec file not found: {spec_path}')
        raise SystemExit(1)
    
    shutil.copy(spec_path, '.')
    print(f'Copied example spec file to current directory: {spec_path.name}')

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