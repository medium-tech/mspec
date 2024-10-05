import argparse
import random
from pprint import pprint

from sample import verify, from_json, to_json, random_sample_item, example_sample_item
from sample.client import *
from sample.db import *

def data_seed(count:int):
    for _ in range(count):
        db_create_sample_item(random_sample_item())

#
# define arguments
#

parser = argparse.ArgumentParser(description='Sample Python CLI')

parser.add_argument('command', type=str, choices=[
    'data-verify',
    'data-seed',
    'data-example',
    'data-random',
    'db-create',
    'db-read',
    'db-update',
    'db-delete',
    'db-list',
    'client-create',
    'client-read',
    'client-update',
    'client-delete',
    'client-list'
])

parser.add_argument('--id', type=str, default=None)
parser.add_argument('--json', type=str, default=None, help='pass in data as a json string')

parser.add_argument('--offset', type=int, default=0, help='used with pagination')
parser.add_argument('--limit', type=int, default=25, help='used with pagination')
parser.add_argument('--seed', type=int, default=None, help='seed for random data generation')
parser.add_argument('--count', type=int, default=101, help='number of items to seed')

parser.add_argument('--name', type=str, default=None, help='name of the item')
parser.add_argument('--verified', type=bool, default=None, help='whether the item is verified')
parser.add_argument('--color', type=str, choices=['red', 'green', 'blue'], default=None, help='favorite color')
parser.add_argument('--age', type=int, default=None, help='age of the item')
parser.add_argument('--score', type=float, default=None, help='score of the item')
parser.add_argument('--tags', type=str, nargs='+', default=None, help='tags for the item')

#
# parse input
#

args = parser.parse_args()

def get_user_data():
    if args.json is not None:
        return from_json(args.json)
    else:
        user_data = {}
        if args.name is not None:
            user_data['name'] = args.name
        if args.verified is not None:
            user_data['verified'] = args.verified
        if args.color is not None:
            user_data['color'] = args.color
        if args.age is not None:
            user_data['age'] = args.age
        if args.score is not None:
            user_data['score'] = args.score
        if args.tags is not None:
            user_data['tags'] = args.tags
        return user_data
    
if args.seed is not None:
    random.seed(args.seed)

db_init()
client_init()

#
# run program
#

if args.command == 'data-verify':
    result = verify(get_user_data())

elif args.command == 'data-seed':
    result = data_seed(args.count)

elif args.command == 'data-example':
    result = to_json(example_sample_item())

elif args.command == 'data-random':
    result = to_json(random_sample_item())

elif args.command == 'db-create':
    result = db_create_sample_item(get_user_data())

elif args.command == 'db-read':
    result = db_read_sample_item(args.id)

elif args.command == 'db-update':
    result = db_update_sample_item(args.id, get_user_data())

elif args.command == 'db-delete':
    result = db_delete_sample_item(args.id)

elif args.command == 'db-list':
    result = db_list_sample_item(args.offset, args.limit)

elif args.command == 'client-create':
    result = client_create_sample_item(get_user_data())

elif args.command == 'client-read':
    result = client_read_sample_item()

elif args.command == 'client-update':
    result = client_update_sample_item()

elif args.command == 'client-delete':
    result = client_delete_sample_item()

elif args.command == 'client-list':
    result = client_list_sample_item(args.offset, args.limit)

#
# output result
#

if isinstance(result, dict):
    pprint(result)
elif result is None:
    pass
else:
    print(result)
