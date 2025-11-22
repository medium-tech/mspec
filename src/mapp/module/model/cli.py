import json

from mapp.errors import MappError
from mapp.module.model.db import *
from mapp.module.model.http import *
from mapp.module.model.data import convert_data_to_model, new_model_class


def add_model_subparser(subparsers, model_spec):

    model_class = new_model_class(model_spec)

    # 
    # init model cli
    #

    model_kebab_case = model_spec['name']['kebab_case']
    model_parser = subparsers.add_parser(model_kebab_case, help=f'Model: {model_kebab_case}')

    io_subparsers = model_parser.add_subparsers(dest='io', required=True)

    help_parser = io_subparsers.add_parser('help', help='Show help for this model', aliases=['-h', '--help'])
    help_parser.set_defaults(func=lambda args: model_parser.print_help())

    #
    # http
    #

    http_parser = io_subparsers.add_parser('http', help='Interact with the model via HTTP API')
    http_actions = http_parser.add_subparsers(dest='action', required=True)

    # create #
    create_parser = http_actions.add_parser('create', help='HTTP create')
    create_parser.add_argument('json', help='JSON string for model creation')
    def cli_http_model_create(args):
        try:
            http_model_create(model_class, json.loads(args.json))
        except json.JSONDecodeError as e:
            raise MappError('INVALID_JSON', f'Invalid JSON: {e}')
        
    create_parser.set_defaults(func=cli_http_model_create)

    # read #
    read_parser = http_actions.add_parser('read', help='HTTP read')
    read_parser.add_argument('model_id', help='ID of the model to read')
    read_parser.set_defaults(func=http_model_read)

    # update #
    update_parser = http_actions.add_parser('update', help='HTTP update')
    update_parser.add_argument('model_id', help='ID of the model to update')
    update_parser.add_argument('json', help='JSON string for model update')
    update_parser.set_defaults(func=http_model_update)

    # delete #
    delete_parser = http_actions.add_parser('delete', help='HTTP delete')
    delete_parser.add_argument('model_id', help='ID of the model to delete')
    delete_parser.set_defaults(func=http_model_delete)

    # list #
    list_parser = http_actions.add_parser('list', help='HTTP list')
    list_parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    list_parser.add_argument('--limit', type=int, default=50, help='Limit for pagination')
    list_parser.set_defaults(func=http_model_list)

    # help #
    http_help_parser = http_actions.add_parser('help', help='Show help for this command', aliases=['-h', '--help'])
    http_help_parser.set_defaults(func=lambda args, p=http_parser: p.print_help())

    #
    # db
    #

    db_parser = io_subparsers.add_parser('db', help='Interact with the model via local SQLite database')
    db_actions = db_parser.add_subparsers(dest='action', required=True)

    # create-table #
    create_table_parser = db_actions.add_parser('create-table', help='Creates the single_model table in the local SQLite database.')
    create_table_parser.set_defaults(func=db_model_create_table)

    # create #
    db_create_parser = db_actions.add_parser('create', help='Creates a single model in the local SQLite database.')
    db_create_parser.add_argument('json', help='JSON string for model creation')
    db_create_parser.set_defaults(func=db_model_create)

    # read #
    db_read_parser = db_actions.add_parser('read', help='Reads a single model from the local SQLite database.')
    db_read_parser.add_argument('model_id', help='ID of the model to read')
    db_read_parser.set_defaults(func=db_model_read)

    # update #
    db_update_parser = db_actions.add_parser('update', help='Updates a single model in the local SQLite database.')
    db_update_parser.add_argument('model_id', help='ID of the model to update')
    db_update_parser.add_argument('json', help='JSON string for model update')
    db_update_parser.set_defaults(func=db_model_update)

    # delete #
    db_delete_parser = db_actions.add_parser('delete', help='Deletes a single model from the local SQLite database.')
    db_delete_parser.add_argument('model_id', help='ID of the model to delete')
    db_delete_parser.set_defaults(func=db_model_delete)

    # list #
    db_list_parser = db_actions.add_parser('list', help='Lists models from the local SQLite database with optional pagination.')
    db_list_parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    db_list_parser.add_argument('--limit', type=int, default=50, help='Limit for pagination')
    db_list_parser.set_defaults(func=db_model_list)

    # help #
    db_help_parser = db_actions.add_parser('help', help='Show help for this command', aliases=['-h', '--help'])
    db_help_parser.set_defaults(func=lambda args, p=db_parser: p.print_help())
