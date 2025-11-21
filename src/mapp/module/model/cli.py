
from mapp.module.model.db import *

def add_model_subparser(subparsers, model_spec):
    model_kebab_case = model_spec['name']['kebab_case']
    model_parser = subparsers.add_parser(model_kebab_case, help=f'Model: {model_kebab_case}')

    # Add db/http subparsers
    io_subparsers = model_parser.add_subparsers(dest='io', required=True)

    # HTTP subparser and actions
    http_parser = io_subparsers.add_parser('http', help='Interact with the model via HTTP API')
    http_actions = http_parser.add_subparsers(dest='action', required=True)
    for action in ['create', 'read', 'update', 'delete', 'list']:
        action_parser = http_actions.add_parser(action, help=f'HTTP {action}')
        action_parser.set_defaults(func=placeholder_action)
    # Add help as a regular action
    http_help_parser = http_actions.add_parser('help', help='Show help for this command', aliases=['-h', '--help'])
    http_help_parser.set_defaults(func=lambda args, p=http_parser: p.print_help())

    # DB subparser and actions
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
    # Add help as a regular action
    db_help_parser = db_actions.add_parser('help', help='Show help for this command', aliases=['-h', '--help'])
    db_help_parser.set_defaults(func=lambda args, p=db_parser: p.print_help())

    # Add help at the model level
    help_parser = io_subparsers.add_parser('help', help='Show help for this model', aliases=['-h', '--help'])
    help_parser.set_defaults(func=lambda args: model_parser.print_help())

def placeholder_action(args):
    print(f'[PLACEHOLDER] Would run {getattr(args, "action", None)} for model {getattr(args, "model", None)} in module {getattr(args, "module", None)} via {getattr(args, "io", None)}')
