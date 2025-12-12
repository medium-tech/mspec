import argparse

from mapp.types import *
from mapp.module.op.run import op_create_callable
from mapp.module.op.http import http_run_op
from mapp.context import cli_op_user_input, cli_load_session, cli_write_session, cli_delete_session

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
    param_fields_str = ''
    for p in params:
        param_fields_str += f"\n        :: {p['name']['snake_case']} - {p['type']}"
        if 'enum' in p:
            param_fields_str += f"\n            :: enum choices:"
            for choice in p['enum']:
                param_fields_str += f"\n              - {choice}"

    outputs = op['output'].values()
    output_fields_str = ''
    for o in outputs:
        output_fields_str += f"\n        :: {o['name']['snake_case']} - {o['type']}"
        if 'enum' in o:
            output_fields_str += f"\n            :: enum choices:"
            for choice in o['enum']:
                output_fields_str += f"\n              - {choice}"

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
    http_parser.add_argument('--interactive', '-i', action='store_true', help='Prompt for secure inputs')
    http_parser.add_argument('--show', '-s', action='store_true', help='Show secure fields in output')
    def cli_op_http(ctx, args):
        if args.json == 'help':
            http_parser.print_help()

        else:
            param_class, output_class = new_op_classes(op, module)

            if args.json is None and not args.interactive:
                params = new_op_params(param_class, dict())
            else:
                params = cli_op_user_input(param_class, args.json, args.interactive)

            raw_output = http_run_op(ctx, param_class, output_class, params)

            if args.module == 'auth':
                if args.model == 'login-user':
                    cli_write_session(ctx, raw_output.access_token)
                elif args.model == 'logout-user':
                    cli_delete_session()

            if args.show:
                output = raw_output
            else:
                output = redact_secure_fields(output_class._op_spec['output'], raw_output)

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
    run_parser.add_argument('--interactive', '-i', action='store_true', help='Prompt for secure inputs')
    run_parser.add_argument('--show', '-s', action='store_true', help='Show secure fields in output')
    def cli_op_run(ctx, args):
        if args.json == 'help':
            run_parser.print_help()

        else:
            param_class, output_class = new_op_classes(op, module)
            op_function = op_create_callable(param_class, output_class)

            if args.json is None and not args.interactive:
                params = new_op_params(param_class, dict())
            else:
                params = cli_op_user_input(param_class, args.json, args.interactive)

            raw_output = op_function(ctx, params)
            if args.module == 'auth':
                if args.model == 'login-user':
                    cli_write_session(ctx, raw_output.access_token)
                elif args.model == 'logout-user':
                    cli_delete_session()

            if args.show:
                output = raw_output
            else:
                output = redact_secure_fields(output_class._op_spec['output'], raw_output)
                
            print(to_json(output, sort_keys=True, indent=4))

    run_parser.set_defaults(func=cli_op_run)
