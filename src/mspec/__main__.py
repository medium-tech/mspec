import argparse
from mspec import load_spec
from pprint import pprint

parser = argparse.ArgumentParser(description='MSpec command line interface')
parser.add_argument('command', choices=['spec'],  help='command to run')

args = parser.parse_args()
match args.command:
    case 'spec':
        pprint(load_spec())

    case _:
        print('Unknown command')
        raise SystemExit(1)
