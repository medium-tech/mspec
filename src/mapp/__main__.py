import os
import argparse

from mapp.context import spec_from_env
from mapp.errors import MappError
from mapp.module import cli as module_cli


__all__ = [
    'main'
]


def main(spec:dict):

    # init application cli #

    parser = argparse.ArgumentParser(description='mapp CLI (Python template app)', prog='mapp')
    subparsers = parser.add_subparsers(dest='module', help='Available modules', required=False)

    help_parser = subparsers.add_parser('help', help='Show top-level help', aliases=['-h', '--help'])
    help_parser.set_defaults(func=lambda args: parser.print_help())

    # parsers for each module #

    try:
        spec_modules = spec['modules']
    except KeyError:
        raise MappError('NO_MODULES_DEFINED', 'No modules defined in the spec file.')

    for module in spec_modules.values():
        module_cli.add_module_subparser(subparsers, module)

    # parse args and run program #

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    mapp_spec = spec_from_env()
    main(mapp_spec)
