from core.exceptions import NotFoundError

from sample_module.example_item.model import ExampleItem

import sqlite3

# vars :: {"sample_module": "module.name.snake_case", "example_item": "model.name.snake_case", "ExampleItem": "model.name.pascal_case", "msample": "project.name.snake_case"}

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
    if obj.id is not None:
        raise ValueError('id must be null to create a new item')
    
    obj.validate()
    cursor:sqlite3.Cursor = ctx['db']['cursor']

    # insert :: macro.py_db_create(model)
    # macro :: py_sql_create :: {"example_item": "model_name_snake_case", "('description', 'verified', 'color', 'count', 'score', 'when')": "fields_sql", "VALUES(?, ?, ?, ?, ?, ?)": "sql_values", "obj.description, obj.verified, obj.color, obj.count, obj.score, obj.when.isoformat()": "fields_py"}
    result = cursor.execute(
        "INSERT INTO example_item('description', 'verified', 'color', 'count', 'score', 'when') VALUES(?, ?, ?, ?, ?, ?)",
        (obj.description, obj.verified, obj.color, obj.count, obj.score, obj.when.isoformat())
    )
    assert result.rowcount == 1
    assert result.lastrowid is not None
    obj.id = str(result.lastrowid)
    # macro :: py_sql_create_list :: {"example_item": "model_name_snake_case", "stuff": "field_name"}
    result = cursor.executemany(
        "INSERT INTO example_item_stuff(value, position, example_item_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.stuff))
    )
    # end macro ::
    
    ctx['db']['commit']()
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

    # insert :: macro.py_db_read(model)
    # macro :: py_sql_read :: {"example_item": "model_name_snake_case"}
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    result = cursor.execute(f"SELECT * FROM example_item WHERE id=?", (id,))
    entry = result.fetchone()
    if entry is None:
        raise NotFoundError(f'example item {id} not found')
    # macro :: py_sql_read_list :: {"example_item": "model_name_snake_case", "stuff": "field_name", "row[0]": "item"}
    stuff_cursor = cursor.execute(f"SELECT value FROM example_item_stuff WHERE example_item_id=? ORDER BY position", (id,))
    stuff = [row[0] for row in stuff_cursor.fetchall()]
    # end macro ::
    
    return ExampleItem(
        id=str(entry[0]),
        # replace :: macro.py_sql_convert(model.fields)
        description=entry[1],
        verified=bool(entry[2]),
        color=entry[3],
        count=entry[4],
        score=entry[5],
        stuff=stuff,
        when=entry[6]
        # end replace ::
    ).validate()

def db_update_example_item(ctx:dict, obj:ExampleItem) -> ExampleItem:
    """
    update a example item in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the ExampleItem object to update.

    return :: the ExampleItem object.
    raises :: NotFoundError if the item is not found
    """
    if obj.id is None:
        raise ValueError('id must not be null to update an item')
    
    obj.validate()
    cursor:sqlite3.Cursor = ctx['db']['cursor']

    # insert :: macro.py_db_update(model)
    # macro :: py_sql_update :: {"example_item": "model_name_snake_case", "'description'=?, 'verified'=?, 'color'=?, 'count'=?, 'score'=?, 'when'=?": "fields_sql", "obj.description, obj.verified, obj.color, obj.count, obj.score, obj.when.isoformat()": "fields_py"}
    result = cursor.execute(
        "UPDATE example_item SET 'description'=?, 'verified'=?, 'color'=?, 'count'=?, 'score'=?, 'when'=? WHERE id=?",
        (obj.description, obj.verified, obj.color, obj.count, obj.score, obj.when.isoformat(), obj.id)
    )
    if result.rowcount == 0:
        raise NotFoundError(f'example item {obj.id} not found')
    # macro :: py_sql_update_list :: {"example_item": "model_name_snake_case", "stuff": "field_name"}
    cursor.execute(f"DELETE FROM example_item_stuff WHERE example_item_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO example_item_stuff(value, position, example_item_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.stuff))
    )
    # end macro ::
    ctx['db']['commit']()
    return obj

def db_delete_example_item(ctx:dict, id:str) -> None:
    """
    delete a example item from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to delete.
    
    return :: None
    """

    cursor:sqlite3.Cursor = ctx['db']['cursor']
    # insert :: macro.py_db_delete(model)
    # macro :: py_sql_delete :: {"example_item": "model_name_snake_case"}
    cursor.execute(f"DELETE FROM example_item WHERE id=?", (id,))
    # macro :: py_sql_delete_list :: {"example_item": "model_name_snake_case", "stuff": "field_name"}
    cursor.execute(f"DELETE FROM example_item_stuff WHERE example_item_id=?", (id,))
    # end macro ::
    ctx['db']['commit']()

def db_list_example_item(ctx:dict, offset:int=0, limit:int=25) -> list[ExampleItem]:
    """
    list example items from the database, and verify each

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.
    
    return :: list of each item as a dict.
    """
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    
    items = []
    query = cursor.execute("SELECT * FROM example_item ORDER BY id LIMIT ? OFFSET ?", (limit, offset))

    for entry in query.fetchall():
        # insert :: macro.py_db_list_lists(model)
        # macro :: py_sql_list_list :: {"example_item": "model_name_snake_case", "stuff": "field_name", "row[0]": "item"}
        stuff_cursor = cursor.execute(f"SELECT value FROM example_item_stuff WHERE example_item_id=? ORDER BY position", (entry[0],))
        stuff = [row[0] for row in stuff_cursor.fetchall()]
        # end macro ::
        items.append(ExampleItem(
            id=str(entry[0]),
            # replace :: macro.py_sql_convert(model.fields)
            description=entry[1],
            verified=bool(entry[2]),
            color=entry[3],
            count=entry[4],
            score=entry[5],
            stuff=stuff,
            when=entry[6]
            # end replace ::
        ).validate())

    return items
