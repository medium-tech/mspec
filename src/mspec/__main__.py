import argparse
import shutil
import json
from mspec import load_spec, sample_spec_dir, builtin_spec_files, load_browser2_spec
from mspec.markup import lingo_app, render_output, lingo_update_state

parser = argparse.ArgumentParser(description='MSpec command line interface')
parser.add_argument('command', choices=['show', 'specs', 'example', 'run'], help='command to run')
parser.add_argument('spec', type=str, help='spec file pattern', default=None, nargs='?')

args = parser.parse_args()

if args.command == 'show':
    if args.spec.endswith('.json'):
        print(json.dumps(load_browser2_spec(args.spec), indent=4))
    else:
        print(json.dumps(load_spec(args.spec), indent=4))

elif args.command == 'specs':
    specs = builtin_spec_files()

    print('Available browser2 spec files:')
    for spec in specs:
        if spec.endswith('json'):
            print(f' - {spec}')

    print('Available mspec template app spec files:')
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