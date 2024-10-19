from sample.sample_item import *
from core.exceptions import NotFoundError
from bson import ObjectId

# vars :: {"sample": "module.name.snake_case", "sample_item": "model.name.snake_case", "mongodb://127.0.0.1:27017": "db.default_url"}

__all__ = [
    'db_create_sample_item', 
    'db_read_sample_item',
    'db_update_sample_item', 
    'db_delete_sample_item', 
    'db_list_sample_item',
]

def db_create_sample_item(ctx:dict, data:dict) -> str:
    """
    create a sample item in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        data :: the data to create the item with.

    return :: the id of the created item.
    """
    result = ctx['db']['client']['sample']['sample_item'].insert_one(sample_item_verify(data))
    return str(result.inserted_id)

def db_read_sample_item(ctx:dict, id:str) -> dict|None:
    """
    read a sample item from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to read.
    
    return :: dict of the item if it exists, None otherwise.
    """
    sample_items = ctx['db']['client']['sample']['sample_item']
    db_entry = sample_items.find_one({'_id': ObjectId(id)})
    if db_entry is None:
        raise NotFoundError(f'sample item {id} not found')
    else:
        db_entry['id'] = str(db_entry.pop('_id'))
        return sample_item_verify(db_entry)


def db_update_sample_item(ctx:dict, id:str, data:dict) -> None:
    """
    update a sample item in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to update.
        data :: the data to update the item with.

    return :: None
    """
    ctx['db']['client']['sample']['sample_item'].update_one({'_id': ObjectId(id)}, {'$set': sample_item_verify(data)})

def db_delete_sample_item(ctx:dict, id:str) -> None:
    """
    delete a sample item from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to delete.
    
    return :: None
    """

    ctx['db']['client']['sample']['sample_item'].delete_one({'_id': ObjectId(id)})

def db_list_sample_item(ctx:dict, offset:int=0, limit:int=25) -> list[dict]:
    """
    list sample items from the database, and verify each

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.
    
    return :: list of each item as a dict.
    """
    sample_items = ctx['db']['client']['sample']['sample_item'].find().skip(offset).limit(limit)
    items = []
    for item in sample_items:
        item['id'] = str(item.pop('_id'))
        items.append(sample_item_verify(item))
    return items
