import argparse

from mapp.types import *
from mapp.errors import MappError

__all__ = [
	'add_op_subparser'
]

def add_op_subparser(subparsers, spec:dict, module: dict, op:dict):

    # 
    # init ops cli
    #

    project_name = spec['project']['name']['kebab_case']
    module_kebab_case = module['name']['kebab_case']
    op_kebab_case = op['name']['kebab_case']

    op_path = f':: {project_name} :: {module_kebab_case} :: {op_kebab_case}'

    param_fields = [f"\n        :: {param['name']['snake_case']} - {param['type']}" for param in op['params'].values()]
    param_fields_str = ''.join(param_fields)

    output_fields = [f"\n        :: {output['name']['snake_case']} - {output['type']}" for output in op['output'].values()]
    output_fields_str = ''.join(output_fields)

    op_docs = '\n    :: params' + param_fields_str + '\n    :: output' + output_fields_str

    op_parser = subparsers.add_parser(
        op_kebab_case, 
        help=f'Operation: {op_kebab_case}', 
        description=op_path + op_docs, 
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    io_subparsers = op_parser.add_subparsers(dest='io', required=True)

    help_parser = io_subparsers.add_parser(
        'help', 
        help='Show help for this operation', 
        aliases=['-h', '--help']
    )
    help_parser.set_defaults(func=lambda ctx, args: op_parser.print_help())

    #
    # http
    #

    http_desc = op_path + ' :: http'

    http_parser = io_subparsers.add_parser(
        'http', 
        help='Run operation via HTTP API',
        description=http_desc + op_docs,
        formatter_class=argparse.RawTextHelpFormatter
    )
    http_parser.add_argument('json', help='JSON string for operation input')
    def cli_op_http(ctx, args):
        if args.json == 'help':
            http_parser.print_help()
        else:
            print('placeholder for http op call')

    http_parser.set_defaults(func=cli_op_http)

    #
    # run
    #

    run_desc = op_path + ' :: run'

    run_parser = io_subparsers.add_parser(
        'run', 
        help='Run operation locally',
        description=run_desc + op_docs,
        formatter_class=argparse.RawTextHelpFormatter
    )
    run_parser.add_argument('json', help='JSON string for operation input')
    def cli_op_run(ctx, args):
        if args.json == 'help':
            run_parser.print_help()
        else:
            print('placeholder for local op run')

    run_parser.set_defaults(func=cli_op_run)
