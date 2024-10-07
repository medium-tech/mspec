import argparse
import random
from pprint import pprint

from sample import *
from sample.client import *
from sample.db import *

#
# define arguments
#

# vars :: {"mspec":"project.snake_case", "sample":"module.snake_case"}
parser = argparse.ArgumentParser(description='mspec - sample - cli')

parser.add_argument('command', type=str, choices=[
    'data-seed',
    # for :: {% for model in module.models %} :: {"sample-item": "model.kebab_case"}
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

db_init()
client_init()

#
# run program
#

if args.command == 'data-seed':
    result = seed_data(args.count)

# for :: {% for model in module.models %} :: {"sample-item": "model.kebab_case", "sample_item": "model.snake_case"}
elif args.command == 'verify-sample-item':
    result = sample_item_verify(get_user_data())

elif args.command == 'random-sample-item':
    result = sample_item_to_json(sample_item_random())

elif args.command == 'example-sample-item':
    result = sample_item_to_json(sample_item_example())

elif args.command == 'db-create-sample-item':
    result = db_create_sample_item(get_user_data())

elif args.command == 'db-read-sample-item':
    result = db_read_sample_item(args.id)

elif args.command == 'db-update-sample-item':
    result = db_update_sample_item(args.id, get_user_data())

elif args.command == 'db-delete-sample-item':
    result = db_delete_sample_item(args.id)

elif args.command == 'db-list-sample-item':
    result = db_list_sample_item(args.offset, args.limit)

elif args.command == 'client-create-sample-item':
    result = client_create_sample_item(get_user_data())

elif args.command == 'client-read-sample-item':
    result = client_read_sample_item()

elif args.command == 'client-update-sample-item':
    result = client_update_sample_item()

elif args.command == 'client-delete-sample-item':
    result = client_delete_sample_item()

elif args.command == 'client-list-sample-item':
    result = client_list_sample_item(args.offset, args.limit)
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
