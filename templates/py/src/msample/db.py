from msample import from_json, to_json, verify
from pymongo import MongoClient
from bson import ObjectId

__all__ = ['db_init', 'db_create_sample_item', 'db_read_sample_item', 'db_update_sample_item', 'db_delete_sample_item', 'db_list_sample_item']

db_client = None

def db_init(client:MongoClient=None) -> None:
    """
    initialize the database client.

    args ::
        client :: the client to use, if None, a new client will be created with default settings.
    
    return :: None
    """
    global db_client
    if client is None:
        db_client = MongoClient()
    else:
        db_client = client

def db_create_sample_item(data:dict) -> str:
    """
    create a sample item in the database, verifying the data first.

    args ::
        data :: the data to create the item with.

    return :: the id of the created item.
    """
    result = db_client['sample']['sample_item'].insert_one(verify(data))
    return str(result.inserted_id)

def db_read_sample_item(id:str) -> dict|None:
    """
    read a sample item from the database and verify it.

    args ::
        id :: the id of the item to read.
    
    return :: dict of the item if it exists, None otherwise.
    """
    sample_items = db_client['sample']['sample_item']
    return verify(sample_items.find_one({'_id': ObjectId(id)}))

def db_update_sample_item(id:str, data:dict) -> None:
    """
    update a sample item in the database, and verify the data first.

    args ::
        id :: the id of the item to update.
        data :: the data to update the item with.

    return :: None
    """
    db_client['sample']['sample_item'].update_one({'_id': ObjectId(id)}, {'$set': verify(data)})

def db_delete_sample_item(id:str) -> None:
    """
    delete a sample item from the database.

    args ::
        id :: the id of the item to delete.
    
    return :: None
    """

    db_client['sample']['sample_item'].delete_one({'_id': ObjectId(id)})

def db_list_sample_item(offset:int=0, limit:int=25) -> list[dict]:
    """
    list sample items from the database, and verify each

    args ::
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.
    
    return :: list of each item as a dict.
    """
    sample_items = db_client['sample']['sample_item'].find().skip(offset).limit(limit)
    return [verify(item) for item in sample_items]