import argparse

from mapp.types import *
from mapp.module.op.run import op_create_callable
from mapp.module.op.http import http_run_op
from mapp.types import json_to_op_params_w_convert

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

    # create help text #

    op_path = f':: {project_name} :: {module_kebab_case} :: {op_kebab_case}'

    params = op['params'].values()
    param_fields = [f"\n        :: {p['name']['snake_case']} - {p['type']}" for p in params]
    param_fields_str = ''.join(param_fields)

    outputs = op['output'].values()
    output_fields = [f"\n        :: {o['name']['snake_case']} - {o['type']}" for o in outputs]
    output_fields_str = ''.join(output_fields)

    op_docs = '\n    :: params' + param_fields_str + '\n    :: output' + output_fields_str

    # list of ops at module level #

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
    # run op via http
    #

    http_desc = op_path + ' :: http'

    http_parser = io_subparsers.add_parser(
        'http', 
        help='Run operation via HTTP API',
        description=http_desc + op_docs,
        formatter_class=argparse.RawTextHelpFormatter
    )
    http_parser.add_argument('json', nargs='?', help='JSON string for operation input')
    def cli_op_http(ctx, args):
        if args.json == 'help':
            http_parser.print_help()
        else:
            param_class, output_class = new_op_classes(op, module)

            if args.json is None:
                params = new_op_params(param_class, dict())
            else:
                params = json_to_op_params_w_convert(args.json, param_class)

            output = http_run_op(ctx, param_class, output_class, params)

            print(to_json(output, sort_keys=True, indent=4))

    http_parser.set_defaults(func=cli_op_http)

    #
    # run op locally
    #

    run_desc = op_path + ' :: run'

    run_parser = io_subparsers.add_parser(
        'run', 
        help='Run operation locally',
        description=run_desc + op_docs,
        formatter_class=argparse.RawTextHelpFormatter
    )
    run_parser.add_argument('json', nargs='?', help='JSON string for operation input')
    def cli_op_run(ctx, args):
        if args.json == 'help':
            run_parser.print_help()

        else:
            param_class, output_class = new_op_classes(op, module)
            op_function = op_create_callable(param_class, output_class)

            if args.json is None:
                params = new_op_params(param_class, dict())
            else:
                params = json_to_op_params_w_convert(param_class, args.json)

            output = op_function(ctx, params)

            print(to_json(output, sort_keys=True, indent=4))

    run_parser.set_defaults(func=cli_op_run)
