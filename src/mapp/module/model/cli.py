import json

from mapp.types import convert_data_to_model, new_model_class
from mapp.errors import MappError
from mapp.module.model.db import *
from mapp.module.model.http import *

__all__ = [
    'add_model_subparser'
]


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
            data = json.loads(args.json)
        except json.JSONDecodeError as e:
            raise MappError('INVALID_JSON', f'Invalid JSON: {e}')
        
        incoming_model = convert_data_to_model(model_class, data)
        http_model_create(model_class, incoming_model)

    create_parser.set_defaults(func=cli_http_model_create)

    # read #
    read_parser = http_actions.add_parser('read', help='HTTP read')
    read_parser.add_argument('model_id', type=str, help='ID of the model to read')
    def cli_http_model_read(args):
        http_model_read(model_class, args.model_id)

    read_parser.set_defaults(func=cli_http_model_read)

    # update #
    update_parser = http_actions.add_parser('update', help='HTTP update')
    update_parser.add_argument('model_id', type=str, help='ID of the model to update')
    update_parser.add_argument('json', help='JSON string for model update')
    def cli_http_model_update(args):
        try:
            data = json.loads(args.json)
        except json.JSONDecodeError as e:
            raise MappError('INVALID_JSON', f'Invalid JSON: {e}')
        incoming_model = convert_data_to_model(model_class, data)
        http_model_update(model_class, args.model_id, incoming_model)
        
    update_parser.set_defaults(func=cli_http_model_update)

    # delete #
    delete_parser = http_actions.add_parser('delete', help='HTTP delete')
    delete_parser.add_argument('model_id', type=str, help='ID of the model to delete')
    def cli_http_model_delete(args):
        http_model_delete(model_class, args.model_id)

    delete_parser.set_defaults(func=cli_http_model_delete)

    # list #
    list_parser = http_actions.add_parser('list', help='HTTP list')
    list_parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    list_parser.add_argument('--limit', type=int, default=50, help='Limit for pagination')
    def cli_http_model_list(args):
        http_model_list(model_class, offset=args.offset, limit=args.limit)
        
    list_parser.set_defaults(func=cli_http_model_list)

    # help #
    http_help_parser = http_actions.add_parser('help', help='Show help for this command', aliases=['-h', '--help'])
    http_help_parser.set_defaults(func=lambda args, p=http_parser: p.print_help())

    #
    # db
    #

    db_parser = io_subparsers.add_parser('db', help='Interact with the model via local SQLite database')
    db_actions = db_parser.add_subparsers(dest='action', required=True)


    # create-table #
    create_table_parser = db_actions.add_parser('create-table', help='Creates the model table in the local SQLite database.')
    def cli_db_model_create_table(args):
        db_model_create_table(model_class)
    create_table_parser.set_defaults(func=cli_db_model_create_table)

    # create #
    db_create_parser = db_actions.add_parser('create', help='Creates a single model in the local SQLite database.')
    db_create_parser.add_argument('json', help='JSON string for model creation')
    def cli_db_model_create(args):
        try:
            data = json.loads(args.json)
        except json.JSONDecodeError as e:
            raise MappError('INVALID_JSON', f'Invalid JSON: {e}')
        incoming_model = convert_data_to_model(model_class, data)
        db_model_create(model_class, incoming_model)
    db_create_parser.set_defaults(func=cli_db_model_create)

    # read #
    db_read_parser = db_actions.add_parser('read', help='Reads a single model from the local SQLite database.')
    db_read_parser.add_argument('model_id', type=str, help='ID of the model to read')
    def cli_db_model_read(args):
        db_model_read(model_class, args.model_id)
    db_read_parser.set_defaults(func=cli_db_model_read)

    # update #
    db_update_parser = db_actions.add_parser('update', help='Updates a single model in the local SQLite database.')
    db_update_parser.add_argument('model_id', type=str, help='ID of the model to update')
    db_update_parser.add_argument('json', help='JSON string for model update')
    def cli_db_model_update(args):
        try:
            data = json.loads(args.json)
        except json.JSONDecodeError as e:
            raise MappError('INVALID_JSON', f'Invalid JSON: {e}')
        incoming_model = convert_data_to_model(model_class, data)
        db_model_update(model_class, args.model_id, incoming_model)
    db_update_parser.set_defaults(func=cli_db_model_update)

    # delete #
    db_delete_parser = db_actions.add_parser('delete', help='Deletes a single model from the local SQLite database.')
    db_delete_parser.add_argument('model_id', type=str, help='ID of the model to delete')
    def cli_db_model_delete(args):
        db_model_delete(model_class, args.model_id)
    db_delete_parser.set_defaults(func=cli_db_model_delete)

    # list #
    db_list_parser = db_actions.add_parser('list', help='Lists models from the local SQLite database with optional pagination.')
    db_list_parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    db_list_parser.add_argument('--limit', type=int, default=50, help='Limit for pagination')
    def cli_db_model_list(args):
        db_model_list(model_class, offset=args.offset, limit=args.limit)
    db_list_parser.set_defaults(func=cli_db_model_list)

    # help #
    db_help_parser = db_actions.add_parser('help', help='Show help for this command', aliases=['-h', '--help'])
    db_help_parser.set_defaults(func=lambda args, p=db_parser: p.print_help())
