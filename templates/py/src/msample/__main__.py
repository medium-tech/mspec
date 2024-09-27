import argparse
from pprint import pprint
from . db import db_create, db_read, db_update, db_delete, db_list
from . data import verify, from_json

#
# arg parser
#

parser = argparse.ArgumentParser(description='Sample Python CLI')

parser.add_argument('command', type=str, choices=['verify', 'create', 'read', 'update', 'delete', 'list'])

parser.add_argument('--id', type=str)
parser.add_argument('--json', type=str)

parser.add_argument('--offset', type=int, default=0)
parser.add_argument('--limit', type=int, default=25)

parser.add_argument('--name', type=str)
parser.add_argument('--verified', type=bool)
parser.add_argument('--color', type=str, choices=['red', 'green', 'blue'])
parser.add_argument('--age', type=int)
parser.add_argument('--score', type=float)
parser.add_argument('--tags', type=str, nargs='+')

#
# parse args
#

args = parser.parse_args()

def get_user_data():
    if args.json is not None:
        data = from_json(args.json)
    else:
        data = {
            'name': args.name,
            'verified': args.verified,
            'color': args.color,
            'age': args.age,
            'score': args.score,
            'tags': args.tags
        }

#
# run program
#

if args.command == 'verify':
    verify(get_user_data())
elif args.command == 'create':
    pprint(db_create(get_user_data()))
elif args.command == 'read':
    pprint(db_read(args.id))
elif args.command == 'update':
    db_update(args.id, get_user_data())
elif args.command == 'delete':
    pprint(db_delete(args.id))
elif args.command == 'list':
    pprint(db_list(args.offset, args.limit))
