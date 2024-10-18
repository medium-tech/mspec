import argparse
import random
from pprint import pprint
from core.db import create_db_context
from core.client import create_client_context
from sample import sample_db, sample_client
# for :: {% for model in module.models.values() %} :: {"sample_item": "model.name.snake_case"}
from sample.sample_item import *
# end for ::

#
# define arguments
#

# vars :: {"mspec":"project.name.snake_case", "sample":"module.name.snake_case"}
parser = argparse.ArgumentParser(description='mspec - sample - cli')

parser.add_argument('command', type=str, choices=[
    'data-seed',
    # for :: {% for model in module.models.values() %} :: {"sample-item": "model.name.kebab_case"}
    'verify-sample-item',
    'random-sample-item',
    'example-sample-item',
    'db-create-sample-item',
    'db-read-sample-item',
    'db-update-sample-item',
    'db-delete-sample-item',
    'db-list-sample-item',
    'client-create-sample-item',
    'client-read-sample-item',
    'client-update-sample-item',
    'client-delete-sample-item',
    'client-list-sample-item',
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
        return sample_item_from_json(args.json)
    
if args.seed is not None:
    random.seed(args.seed)

cli_ctx = {}
cli_ctx.update(create_db_context())
cli_ctx.update(create_client_context())


#
# run program
#

if args.command == 'data-seed':
    result = sample_db.seed_data(cli_ctx, args.count)

# for :: {% for model in module.models.values() %} :: {"sample-item": "model.name.kebab_case", "sample_item": "model.name.snake_case"}
elif args.command == 'verify-sample-item':
    result = sample_item_verify(get_user_data())

elif args.command == 'random-sample-item':
    result = sample_item_to_json(sample_item_random())

elif args.command == 'example-sample-item':
    result = sample_item_to_json(sample_item_example())

elif args.command == 'db-create-sample-item':
    result = sample_db.create_sample_item(cli_ctx, get_user_data())

elif args.command == 'db-read-sample-item':
    result = sample_db.read_sample_item(cli_ctx, args.id)

elif args.command == 'db-update-sample-item':
    result = sample_db.update_sample_item(cli_ctx, args.id, get_user_data())

elif args.command == 'db-delete-sample-item':
    result = sample_db.delete_sample_item(cli_ctx, args.id)

elif args.command == 'db-list-sample-item':
    result = sample_db.list_sample_item(cli_ctx, args.offset, args.limit)

elif args.command == 'client-create-sample-item':
    result = sample_client.create_sample_item(cli_ctx, get_user_data())

elif args.command == 'client-read-sample-item':
    result = sample_client.read_sample_item(cli_ctx, )

elif args.command == 'client-update-sample-item':
    result = sample_client.update_sample_item(cli_ctx, )

elif args.command == 'client-delete-sample-item':
    result = sample_client.delete_sample_item(cli_ctx, )

elif args.command == 'client-list-sample-item':
    result = sample_client.list_sample_item(cli_ctx, args.offset, args.limit)
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
