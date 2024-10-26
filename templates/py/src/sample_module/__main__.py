import argparse
import random
from pprint import pprint
from core.db import create_db_context
from core.client import create_client_context
from sample_module import sample_module_db, sample_module_client
# for :: {% for model in module.models.values() %} :: {"example_item": "model.name.snake_case"}
from sample_module.example_item import *
# end for ::

#
# define arguments
#

# vars :: {"mspec":"project.name.snake_case", "sample_module":"module.name.snake_case", "sample module":"module.name.lower_case"}
parser = argparse.ArgumentParser(description='mspec - sample module - cli')

parser.add_argument('command', type=str, choices=[
    'data-seed',
    # for :: {% for model in module.models.values() %} :: {"example-item": "model.name.kebab_case"}
    'verify-example-item',
    'random-example-item',
    'example-example-item',
    'db-create-example-item',
    'db-read-example-item',
    'db-update-example-item',
    'db-delete-example-item',
    'db-list-example-item',
    'client-create-example-item',
    'client-read-example-item',
    'client-update-example-item',
    'client-delete-example-item',
    'client-list-example-item',
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

def get_user_data():
    if args.json is None:
        raise Exception('must supply data via json argument')
    else:
        return example_item_from_json(args.json)
    
if args.seed is not None:
    random.seed(args.seed)

cli_ctx = {}
cli_ctx.update(create_db_context())
cli_ctx.update(create_client_context())


#
# run program
#

if args.command == 'data-seed':
    result = sample_module_db.seed_data(cli_ctx, args.count)

# for :: {% for model in module.models.values() %} :: {"example-item": "model.name.kebab_case", "example_item": "model.name.snake_case"}
elif args.command == 'verify-example-item':
    result = example_item_verify(get_user_data())

elif args.command == 'random-example-item':
    result = example_item_to_json(example_item_random())

elif args.command == 'example-example-item':
    result = example_item_to_json(example_item_example())

elif args.command == 'db-create-example-item':
    result = sample_module_db.create_example_item(cli_ctx, get_user_data())

elif args.command == 'db-read-example-item':
    result = sample_module_db.read_example_item(cli_ctx, args.id)

elif args.command == 'db-update-example-item':
    result = sample_module_db.update_example_item(cli_ctx, args.id, get_user_data())

elif args.command == 'db-delete-example-item':
    result = sample_module_db.delete_example_item(cli_ctx, args.id)

elif args.command == 'db-list-example-item':
    result = sample_module_db.list_example_item(cli_ctx, args.offset, args.limit)

elif args.command == 'client-create-example-item':
    result = sample_module_client.create_example_item(cli_ctx, get_user_data())

elif args.command == 'client-read-example-item':
    result = sample_module_client.read_example_item(cli_ctx, )

elif args.command == 'client-update-example-item':
    result = sample_module_client.update_example_item(cli_ctx, )

elif args.command == 'client-delete-example-item':
    result = sample_module_client.delete_example_item(cli_ctx, )

elif args.command == 'client-list-example-item':
    result = sample_module_client.list_example_item(cli_ctx, args.offset, args.limit)
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
