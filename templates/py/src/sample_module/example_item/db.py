from sample_module.example_item.model import ExampleItem
from core.exceptions import NotFoundError

from pymongo.collection import Collection
from bson import ObjectId

# vars :: {"sample_module": "module.name.snake_case", "example_item": "model.name.snake_case", "ExampleItem": "model.name.pascal_case". "msample": "project.name.snake_case"}

__all__ = [
    'db_create_example_item', 
    'db_read_example_item',
    'db_update_example_item', 
    'db_delete_example_item', 
    'db_list_example_item',
]

def db_create_example_item(ctx:dict, obj:ExampleItem) -> ExampleItem:
    """
    create a example item in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the ExampleItem object to create.

    return :: and ExampleItem object with the new id.
    """
    example_items:Collection = ctx['db']['client']['msample']['sample_module.example_item']
    result = example_items.insert_one(obj.validate().to_dict())
    obj.id = str(result.inserted_id)
    return obj

def db_read_example_item(ctx:dict, id:str) -> ExampleItem:
    """
    read a example item from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to read.
    
    return :: the ExampleItem object.
    raises :: NotFoundError if the item is not found.
    """
    example_items:Collection = ctx['db']['client']['msample']['sample_module.example_item']
    db_entry = example_items.find_one({'_id': ObjectId(id)})
    if db_entry is None:
        raise NotFoundError(f'example item {id} not found')
    else:
        db_entry['id'] = str(db_entry.pop('_id'))
        return ExampleItem(**db_entry).validate()

def db_update_example_item(ctx:dict, obj:ExampleItem) -> ExampleItem:
    """
    update a example item in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the ExampleItem object to update.

    return :: the ExampleItem object.
    raises :: NotFoundError if the item is not found
    """
    data = obj.validate().to_dict()
    _id = data.pop('id')

    example_items:Collection = ctx['db']['client']['msample']['sample_module.example_item']
    result = example_items.update_one({'_id': ObjectId(_id)}, {'$set': data})
    if result.matched_count == 0:
        raise NotFoundError(f'example item {_id} not found')
    
    return obj

def db_delete_example_item(ctx:dict, id:str) -> None:
    """
    delete a example item from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to delete.
    
    return :: None
    """

    example_items:Collection = ctx['db']['client']['msample']['sample_module.example_item']
    example_items.delete_one({'_id': ObjectId(id)})

def db_list_example_item(ctx:dict, offset:int=0, limit:int=25) -> list[ExampleItem]:
    """
    list example items from the database, and verify each

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.
    
    return :: list of each item as a dict.
    """
    example_items:Collection = ctx['db']['client']['msample']['sample_module.example_item']
    items = []

    for item in example_items.find(skip=offset, limit=limit):
        item['id'] = str(item.pop('_id'))
        items.append(ExampleItem(**item).validate())

    return items
