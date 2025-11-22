from mapp.module.model.db import *
from mapp.module.model.http import *

def add_model_subparser(subparsers, model_spec):

    # init model cli #

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
    create_parser.set_defaults(func=http_model_create)

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
    db_action_map = [
        ('create-table', 'Creates the single_model table in the local SQLite database.', db_model_create_table),
        ('create', 'Creates a single model in the local SQLite database.', db_model_create),
        ('read', 'Reads a single model from the local SQLite database.', db_model_read),
        ('update', 'Updates a single model in the local SQLite database.', db_model_update),
        ('delete', 'Deletes a single model from the local SQLite database.', db_model_delete),
        ('list', 'Lists models from the local SQLite database with optional pagination.', db_model_list)
    ]
    for action, help_text, func in db_action_map:
        action_parser = db_actions.add_parser(action, help=help_text)
        action_parser.set_defaults(func=func)
    
    db_help_parser = db_actions.add_parser('help', help='Show help for this command', aliases=['-h', '--help'])
    db_help_parser.set_defaults(func=lambda args, p=db_parser: p.print_help())

