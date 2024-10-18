import argparse
from mspec import load_spec
from pprint import pprint

parser = argparse.ArgumentParser(description='MSpec command line interface')
parser.add_argument('command', choices=['spec'],  help='command to run')
parser.add_argument('--spec', type=str, default='test-gen.yaml', help='spec file pattern')

args = parser.parse_args()
match args.command:
    case 'spec':
        pprint(load_spec(args.spec))

    case _:
        print('Unknown command')
        raise SystemExit(1)
