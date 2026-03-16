import argparse
import json
import sys
import atexit

from mapp.context import MappContext, spec_from_env, get_context_from_env, get_cli_access_token
from mapp.errors import MappError
from mapp.db import create_tables
from mapp.module import cli as module_cli


__all__ = [
    'main'
]


def main(ctx: MappContext, spec:dict):

    # init application cli #

    project_name = spec['project']['name']['kebab_case']

    parser = argparse.ArgumentParser(
        prog='mapp',
        description=f':: {project_name}', 
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--log', action='store_true', help='Enable logging output to console')
    parser.add_argument('--file-input', '-fi', type=str, help='Path to file input for ops that support file input, or - for stdin', default=None)
    parser.add_argument('--file-output', '-fo', type=str, help='Path to write file output for ops that support file output, or - for stdout', default=None)
    subparsers = parser.add_subparsers(dest='module', help='Available modules', required=False)

    help_parser = subparsers.add_parser('help', help='Show top-level help', aliases=['-h', '--help'])
    help_parser.set_defaults(func=lambda ctx, args: parser.print_help())

    create_tables_parser = subparsers.add_parser(
        'create-tables', 
        help='Create all tables for app', 
        description=f':: {project_name} :: create-tables'
    )
    create_tables_parser.add_argument('help', nargs='?', help='Show help for this command')
    def cli_create_tables(ctx, args):
        if args.help == 'help':
            create_tables_parser.print_help()
        else:
            ack = create_tables(ctx, spec)
            # return ack
            print(json.dumps(ack.to_dict(), sort_keys=True, indent=4))
    create_tables_parser.set_defaults(func=cli_create_tables)

    # parsers for each module #

    try:
        spec_modules = spec['modules']
    except KeyError:
        raise MappError('NO_MODULES_DEFINED', 'No modules defined in the spec file.')

    for module in spec_modules.values():
        if module.get('hidden', False) is True:
            continue
        module_cli.add_module_subparser(subparsers, spec, module)

    # parse args and run program #

    args = parser.parse_args()

    if args.log is True:
        ctx.log = cli_logging
    
    if args.file_input is not None:
        if args.file_input == '-':
            ctx.log(':: reading file input from stdin')
            ctx.self = {'file_input': sys.stdin.buffer.read(), 'file_input_name': 'stdin.bin'}
        else:
            with open(args.file_input, 'rb') as f:
                ctx.self = {'file_input': f.read(), 'file_input_name': args.file_input}

    if args.file_output is not None:
        if args.file_output == '-':
            ctx.self['file_output'] = sys.stdout.buffer
        else:
            ctx.self['file_output'] = open(args.file_output, 'wb+')
            atexit.register(lambda: ctx.self['file_output'].close())

    if hasattr(args, 'func'):
        try:
            args.func(ctx, args)
        except MappError as e:
            print(json.dumps(e.to_dict(), sort_keys=True, indent=4))
            raise SystemExit(1)
    else:
        parser.print_help()

def cli_logging(msg: str):
    print(f':: log :: {msg}')

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

        cli_ctx.current_access_token = lambda: get_cli_access_token(cli_ctx)
        if (token := get_cli_access_token(cli_ctx)) is not None:
            cli_ctx.client.set_bearer_token(token)

        main(cli_ctx, mapp_spec)
