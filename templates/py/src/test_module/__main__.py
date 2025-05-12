import argparse
import random
from pprint import pprint
from core.db import create_db_context
from core.client import create_client_context
# for :: {% for model in module.models.values() %} :: {"test_model": "model.name.snake_case"}
from test_module.test_model.client import *
from test_module.test_model.db import *
from test_module.test_model.model import *
# end for ::

# vars :: {"unit_test":"project.name.snake_case", "test_module":"module.name.snake_case", "test module":"module.name.lower_case"}

#
# define arguments
#


parser = argparse.ArgumentParser(description='unit_test - test module - cli')

parser.add_argument('command', type=str, choices=[
    'data-seed',
    # for :: {% for model in module.models.values() %} :: {"test-model": "model.name.kebab_case"}
    'verify-test-model',
    'random-test-model',
    'example-test-model',
    'db-create-test-model',
    'db-read-test-model',
    'db-update-test-model',
    'db-delete-test-model',
    'db-list-test-model',
    'client-create-test-model',
    'client-read-test-model',
    'client-update-test-model',
    'client-delete-test-model',
    'client-list-test-model',
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
        # for :: {% for model in module.models.values() %} :: {"test_model": "model.name.snake_case", "TestModel": "model.name.pascal_case"}
        db_create_test_model(cli_ctx, TestModel.random())
        # end for ::

# for :: {% for model in module.models.values() %} :: {"test-model": "model.name.kebab_case", "test_model": "model.name.snake_case", "TestModel": "model.name.pascal_case"}
elif args.command == 'verify-test-model':
    result = TestModel.from_json(args.json).validate()

elif args.command == 'random-test-model':
    result = TestModel.random().to_json()

elif args.command == 'example-test-model':
    result = TestModel.example().to_json()

elif args.command == 'db-create-test-model':
    if args.json is None:
        raise Exception('must supply data via json argument')
    result = db_create_test_model(cli_ctx, TestModel.from_json(args.json))

elif args.command == 'db-read-test-model':
    result = db_read_test_model(cli_ctx, args.id)

elif args.command == 'db-update-test-model':
    if args.json is None:
        raise Exception('must supply data via json argument')
    result = db_update_test_model(cli_ctx, args.id, TestModel.from_json(args.json))

elif args.command == 'db-delete-test-model':
    result = db_delete_test_model(cli_ctx, args.id)

elif args.command == 'db-list-test-model':
    result = db_list_test_model(cli_ctx, args.offset, args.limit)

elif args.command == 'client-create-test-model':
    if args.json is None:
        raise Exception('must supply data via json argument')
    result = client_create_test_model(cli_ctx, TestModel.from_json(args.json))

elif args.command == 'client-read-test-model':
    result = client_read_test_model(cli_ctx, )

elif args.command == 'client-update-test-model':
    result = client_update_test_model(cli_ctx, )

elif args.command == 'client-delete-test-model':
    result = client_delete_test_model(cli_ctx, )

elif args.command == 'client-list-test-model':
    result = client_list_test_model(cli_ctx, args.offset, args.limit)
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