import argparse
import random
from pprint import pprint
from core.db import create_db_context
from core.client import create_client_context
# for :: {% for model in module.models.values() %} :: {"single_model": "model.name.snake_case"}
from test_module.single_model.client import *
from test_module.single_model.db import *
from test_module.single_model.model import *
# end for ::

# vars :: {"template_app":"project.name.snake_case", "test_module":"module.name.snake_case", "test module":"module.name.lower_case"}

#
# define arguments
#


parser = argparse.ArgumentParser(description='template_app - test module - cli')

parser.add_argument('command', type=str, choices=[
    'data-seed',
    # for :: {% for model in module.models.values() %} :: {"single-model": "model.name.kebab_case"}
    'verify-single-model',
    'random-single-model',
    'example-single-model',
    'db-create-single-model',
    'db-read-single-model',
    'db-update-single-model',
    'db-delete-single-model',
    'db-list-single-model',
    'client-create-single-model',
    'client-read-single-model',
    'client-update-single-model',
    'client-delete-single-model',
    'client-list-single-model',
    # end for ::
])

parser.add_argument('--id', type=str, default=None)
parser.add_argument('--json', type=str, default=None, help='pass in data as a json string')

parser.add_argument('--offset', type=int, default=0, help='used with pagination')
parser.add_argument('--limit', type=int, default=25, help='used with pagination')
parser.add_argument('--seed', type=int, default=None, help='seed for random data generation')
parser.add_argument('--count', type=int, default=101, help='number of items to seed')

#
# parse input
#

args = parser.parse_args()
    
if args.seed is not None:
    random.seed(args.seed)

cli_ctx = {}
cli_ctx.update(create_db_context())
cli_ctx.update(create_client_context())

#
# run program
#

if args.command == 'data-seed':
    for _ in range(args.count):
        # for :: {% for model in module.models.values() %} :: {"single_model": "model.name.snake_case", "SingleModel": "model.name.pascal_case"}
        db_create_single_model(cli_ctx, SingleModel.random())
        # end for ::

# for :: {% for model in module.models.values() %} :: {"single-model": "model.name.kebab_case", "single_model": "model.name.snake_case", "SingleModel": "model.name.pascal_case"}
elif args.command == 'verify-single-model':
    result = SingleModel.from_json(args.json).validate()

elif args.command == 'random-single-model':
    result = SingleModel.random().to_json()

elif args.command == 'example-single-model':
    result = SingleModel.example().to_json()

elif args.command == 'db-create-single-model':
    if args.json is None:
        raise Exception('must supply data via json argument')
    result = db_create_single_model(cli_ctx, SingleModel.from_json(args.json))

elif args.command == 'db-read-single-model':
    result = db_read_single_model(cli_ctx, args.id)

elif args.command == 'db-update-single-model':
    if args.json is None:
        raise Exception('must supply data via json argument')
    result = db_update_single_model(cli_ctx, args.id, SingleModel.from_json(args.json))

elif args.command == 'db-delete-single-model':
    result = db_delete_single_model(cli_ctx, args.id)

elif args.command == 'db-list-single-model':
    result = db_list_single_model(cli_ctx, args.offset, args.limit)

elif args.command == 'client-create-single-model':
    if args.json is None:
        raise Exception('must supply data via json argument')
    result = client_create_single_model(cli_ctx, SingleModel.from_json(args.json))

elif args.command == 'client-read-single-model':
    result = client_read_single_model(cli_ctx, )

elif args.command == 'client-update-single-model':
    result = client_update_single_model(cli_ctx, )

elif args.command == 'client-delete-single-model':
    result = client_delete_single_model(cli_ctx, )

elif args.command == 'client-list-single-model':
    result = client_list_single_model(cli_ctx, args.offset, args.limit)
# end for ::

#
# output result
#

if isinstance(result, dict):
    pprint(result)
elif result is None:
    pass
else:
    print(result)