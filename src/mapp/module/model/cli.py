from mapp.types import *
from mapp.errors import MappError
from mapp.module.model.db import *
from mapp.module.model.http import *

__all__ = [
    'add_model_subparser'
]


def add_model_subparser(subparsers, spec:dict, module: dict, model:dict):

    model_class = new_model_class(model)

    # 
    # init model cli
    #

    project_name = spec['project']['name']['pascal_case']
    module_snake_case = module['name']['snake_case']
    model_snake_case = model['name']['snake_case']
    model_kebab_case = model['name']['kebab_case']

    description = f':: {project_name} :: {module_snake_case} :: {model_snake_case}'

    model_parser = subparsers.add_parser(model_kebab_case, help=f'Model: {model_kebab_case}', description=description)

    io_subparsers = model_parser.add_subparsers(dest='io', required=True)

    help_parser = io_subparsers.add_parser(
        'help', 
        help='Show help for this model', 
        aliases=['-h', '--help']
    )
    help_parser.set_defaults(func=lambda ctx, args: model_parser.print_help())

    #
    # http
    #

    http_desc = description + ' :: http'

    http_parser = io_subparsers.add_parser(
        'http', 
        help='Interact with the model via HTTP API',
        description=http_desc
    )
    http_actions = http_parser.add_subparsers(dest='action', required=True)


    # create #
    create_parser = http_actions.add_parser('create', help='HTTP create', description=http_desc + ' :: create')
    create_parser.add_argument('json', help='JSON string for model creation')
    def cli_http_model_create(ctx, args):        
        incoming_model = convert_json_to_model(model_class, args.json)
        new_model = http_model_create(ctx, model_class, incoming_model)
        print(model_to_json(new_model, sort_keys=True, indent=4))

    create_parser.set_defaults(func=cli_http_model_create)

    # read #
    read_parser = http_actions.add_parser('read', help='HTTP read', description=http_desc + ' :: read')
    read_parser.add_argument('model_id', type=str, help='ID of the model to read')
    def cli_http_model_read(ctx, args):
        model = http_model_read(ctx, model_class, args.model_id)
        print(model_to_json(model, sort_keys=True, indent=4))

    read_parser.set_defaults(func=cli_http_model_read)

    # update #
    update_parser = http_actions.add_parser('update', help='HTTP update', description=http_desc + ' :: update')
    update_parser.add_argument('model_id', type=str, help='ID of the model to update')
    update_parser.add_argument('json', help='JSON string for model update')
    def cli_http_model_update(ctx, args):
        incoming_model = convert_json_to_model(model_class, args.json)
        updated_model = http_model_update(ctx, model_class, args.model_id, incoming_model)
        print(model_to_json(updated_model, sort_keys=True, indent=4))
        
    update_parser.set_defaults(func=cli_http_model_update)

    # delete #
    delete_parser = http_actions.add_parser('delete', help='HTTP delete', description=http_desc + ' :: delete')
    delete_parser.add_argument('model_id', type=str, help='ID of the model to delete')
    def cli_http_model_delete(ctx, args):
        ack = http_model_delete(ctx, model_class, args.model_id)
        print(model_to_json(ack, sort_keys=True, indent=4))

    delete_parser.set_defaults(func=cli_http_model_delete)

    # list #
    list_parser = http_actions.add_parser('list', help='HTTP list', description=http_desc + ' :: list')
    list_parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    list_parser.add_argument('--size', type=int, default=50, help='Page size for pagination')
    def cli_http_model_list(ctx, args):
        result = http_model_list(ctx, model_class, offset=args.offset, size=args.size)
        print(to_json(result, sort_keys=True, indent=4))
    list_parser.set_defaults(func=cli_http_model_list)

    # help #
    http_help_parser = http_actions.add_parser('help', help='Show help for this command', aliases=['-h', '--help'])
    http_help_parser.set_defaults(func=lambda ctx, args, p=http_parser: p.print_help())

    #
    # db
    #

    db_desc = description + ' :: db'
    db_parser = io_subparsers.add_parser(
        'db', 
        help='Interact with the model via local SQLite database', 
        description=db_desc
    )
    db_actions = db_parser.add_subparsers(dest='action', required=True)


    # create-table #
    create_table_parser = db_actions.add_parser(
        'create-table', 
        help='Creates the model table in the local SQLite database.',
        description=db_desc + ' :: create-table'
    )
    def cli_db_model_create_table(ctx, args):
        db_model_create_table(ctx, model_class)
        print(model_to_json({'acknowledged': True}, sort_keys=True, indent=4))
    create_table_parser.set_defaults(func=cli_db_model_create_table)

    # create #
    db_create_parser = db_actions.add_parser(
        'create', 
        help='Creates a single model in the local SQLite database.',
        description=db_desc + ' :: create'
    )
    db_create_parser.add_argument('json', help='JSON string for model creation')
    def cli_db_model_create(ctx, args):
        incoming_model = convert_json_to_model(model_class, args.json)
        new_model = db_model_create(ctx, model_class, incoming_model)
        json_out = model_to_json(new_model, sort_keys=True, indent=4)
        print(json_out)
    db_create_parser.set_defaults(func=cli_db_model_create)

    # read #
    db_read_parser = db_actions.add_parser(
        'read', 
        help='Reads a single model from the local SQLite database.',
        description=db_desc + ' :: read'
    )
    db_read_parser.add_argument('model_id', type=str, help='ID of the model to read')
    def cli_db_model_read(ctx, args):
        model = db_model_read(ctx, model_class, args.model_id)
        print(model_to_json(model, sort_keys=True, indent=4))
    db_read_parser.set_defaults(func=cli_db_model_read)

    # update #
    db_update_parser = db_actions.add_parser(
        'update', 
        help='Updates a single model in the local SQLite database.',
        description=db_desc + ' :: update'
    )
    db_update_parser.add_argument('model_id', type=str, help='ID of the model to update')
    db_update_parser.add_argument('json', help='JSON string for model update')
    def cli_db_model_update(ctx, args):
        incoming_model = convert_json_to_model(model_class, args.json, args.model_id)
        if incoming_model.id is None:
            incoming_model = incoming_model._replace(id=args.model_id)
        elif incoming_model.id != args.model_id:
            raise MappError('ID_MISMATCH', 'Model ID in JSON does not match the provided model_id argument.')
        updated_model = db_model_update(ctx, model_class, incoming_model)
        print(model_to_json(updated_model, sort_keys=True, indent=4))
    db_update_parser.set_defaults(func=cli_db_model_update)

    # delete #
    db_delete_parser = db_actions.add_parser(
        'delete', 
        help='Deletes a single model from the local SQLite database.',
        description=db_desc + ' :: delete'
    )
    db_delete_parser.add_argument('model_id', type=str, help='ID of the model to delete')
    def cli_db_model_delete(ctx, args):
        ack = db_model_delete(ctx, model_class, args.model_id)
        print(to_json(ack, sort_keys=True, indent=4))
    db_delete_parser.set_defaults(func=cli_db_model_delete)

    # list #
    db_list_parser = db_actions.add_parser(
        'list', 
        help='Lists models from the local SQLite database with optional pagination.',
        description=db_desc + ' :: list'
    )
    db_list_parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    db_list_parser.add_argument('--size', type=int, default=50, help='Page size for pagination')
    def cli_db_model_list(ctx, args):
        result = db_model_list(ctx, model_class, offset=args.offset, size=args.size)
        print(to_json(result, sort_keys=True, indent=4))
    db_list_parser.set_defaults(func=cli_db_model_list)

    # help #
    db_help_parser = db_actions.add_parser('help', help='Show help for this command', aliases=['-h', '--help'])
    db_help_parser.set_defaults(func=lambda ctx, args, p=db_parser: p.print_help())