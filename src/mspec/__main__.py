import argparse
from mspec import spec
from pprint import pprint

parser = argparse.ArgumentParser(description='MSpec command line interface')
parser.add_argument('command', choices=['print-spec'],  help='command to run')

args = parser.parse_args()
match args.command:
    case 'print-spec':
        pprint(spec())

    case _:
        print('Unknown command')
        raise SystemExit(1)
