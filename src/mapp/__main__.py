import argparse
import json

from mapp.context import MappContext, spec_from_env, get_context_from_env
from mapp.errors import MappError
from mapp.db import create_tables
from mapp.module import cli as module_cli


__all__ = [
    'main'
]


def main(ctx: MappContext, spec:dict):

    # init application cli #

    project_name = spec['project']['name']['kebab_case']

    parser = argparse.ArgumentParser(description=f':: {project_name}', prog='mapp')
    subparsers = parser.add_subparsers(dest='module', help='Available modules', required=False)

    help_parser = subparsers.add_parser('help', help='Show top-level help', aliases=['-h', '--help'])
    help_parser.set_defaults(func=lambda ctx, args: parser.print_help())

    create_tables_parser = subparsers.add_parser('create-tables', help='Create all tables for app')
    create_tables_parser.set_defaults(func=lambda ctx, args: create_tables(ctx, spec))

    # parsers for each module #

    try:
        spec_modules = spec['modules']
    except KeyError:
        raise MappError('NO_MODULES_DEFINED', 'No modules defined in the spec file.')

    for module in spec_modules.values():
        module_cli.add_module_subparser(subparsers, spec, module)

    # parse args and run program #

    args = parser.parse_args()

    if hasattr(args, 'func'):
        try:
            args.func(ctx, args)
        except MappError as e:
            print(json.dumps(e.to_dict(), sort_keys=True, indent=4))
    else:
        parser.print_help()

if __name__ == "__main__":
    
    try:
        mapp_spec = spec_from_env()
    except MappError as e:
        if e.code == 'SPEC_FILE_NOT_FOUND':
            print(
                ':: ERROR :: SPEC_FILE_NOT_FOUND\n'
                '  :: Set with MAPP_SPEC_FILE env variable.\n'
                '  :: Run "python -m mspec -h" to discover built in example specs.')
        else:
            raise
    else:
        cli_ctx = get_context_from_env()
        main(cli_ctx, mapp_spec)
