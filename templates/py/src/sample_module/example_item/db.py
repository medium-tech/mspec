from sample_module.example_item import *
from core.exceptions import NotFoundError
from bson import ObjectId

# vars :: {"sample_module": "module.name.snake_case", "example_item": "model.name.snake_case", "mongodb://127.0.0.1:27017": "db.default_url", "msample": "project.name.snake_case"}

__all__ = [
    'db_create_example_item', 
    'db_read_example_item',
    'db_update_example_item', 
    'db_delete_example_item', 
    'db_list_example_item',
]

def db_create_example_item(ctx:dict, data:dict) -> str:
    """
    create a example item in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        data :: the data to create the item with.

    return :: str of the id of the created item.
    """
    example_items = ctx['db']['client']['msample']['sample_module.example_item']
    result = example_items.insert_one(example_item_verify(data))
    return str(result.inserted_id)

def db_read_example_item(ctx:dict, id:str) -> dict:
    """
    read a example item from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to read.
    
    return :: dict of the example item
    raises :: NotFoundError if the item is not found.
    """
    example_items = ctx['db']['client']['msample']['sample_module.example_item']
    db_entry = example_items.find_one({'_id': ObjectId(id)})
    if db_entry is None:
        raise NotFoundError(f'example item {id} not found')
    else:
        db_entry['id'] = str(db_entry.pop('_id'))
        return example_item_verify(db_entry)


def db_update_example_item(ctx:dict, data:dict) -> None:
    """
    update a example item in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to update.
        data :: the data to update the item with.

    return :: None
    raises :: NotFoundError if the item is not found
    """
    example_item_verify(data)
    _id = data.pop('id')
    example_items = ctx['db']['client']['msample']['sample_module.example_item']
    result = example_items.update_one({'_id': ObjectId(_id)}, {'$set': data})
    if result.matched_count == 0:
        raise NotFoundError(f'example item {_id} not found')

def db_delete_example_item(ctx:dict, id:str) -> None:
    """
    delete a example item from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to delete.
    
    return :: None
    """

    example_items = ctx['db']['client']['msample']['sample_module.example_item']
    example_items.delete_one({'_id': ObjectId(id)})

def db_list_example_item(ctx:dict, offset:int=0, limit:int=25) -> list[dict]:
    """
    list example items from the database, and verify each

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.
    
    return :: list of each item as a dict.
    """
    example_items = ctx['db']['client']['msample']['sample_module.example_item']
    items = []
    for item in example_items.find().skip(offset).limit(limit):
        item['id'] = str(item.pop('_id'))
        items.append(example_item_verify(item))
    return items
