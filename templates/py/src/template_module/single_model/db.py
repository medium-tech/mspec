import sqlite3
from datetime import datetime
from core.types import datetime_format_str
from core.exceptions import NotFoundError
from template_module.single_model.model import SingleModel

# vars :: {"template_module": "module.name.snake_case", "single_model": "model.name.snake_case", "SingleModel": "model.name.pascal_case"}

__all__ = [
    'db_create_single_model', 
    'db_read_single_model',
    'db_update_single_model', 
    'db_delete_single_model', 
    'db_list_single_model',
]

def db_create_single_model(ctx:dict, obj:SingleModel) -> SingleModel:
    """
    create a single model in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the SingleModel object to create.

    return :: and SingleModel object with the new id.
    """
    if obj.id is not None:
        raise ValueError('id must be null to create a new item')
    
    obj.validate()
    cursor:sqlite3.Cursor = ctx['db']['cursor']

    # insert :: macro.py_db_create(model)
    # macro :: py_sql_create :: {"single_model": "model_name_snake_case", "('single_bool', 'single_datetime', 'single_enum', 'single_float', 'single_int', 'single_string')": "fields_sql", "VALUES(?, ?, ?, ?, ?, ?)": "sql_values", "obj.single_bool, obj.single_datetime.isoformat(), obj.single_enum, obj.single_float, obj.single_int, obj.single_string": "fields_py"}
    result = cursor.execute(
        "INSERT INTO single_model('single_bool', 'single_datetime', 'single_enum', 'single_float', 'single_int', 'single_string') VALUES(?, ?, ?, ?, ?, ?)",
        (obj.single_bool, obj.single_datetime.isoformat(), obj.single_enum, obj.single_float, obj.single_int, obj.single_string)
    )
    assert result.rowcount == 1
    assert result.lastrowid is not None
    obj.id = str(result.lastrowid)
    # end macro ::

    ctx['db']['commit']()
    return obj

def db_read_single_model(ctx:dict, id:str) -> SingleModel:
    """
    read a single model from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to read.
    
    return :: the SingleModel object.
    raises :: NotFoundError if the item is not found.
    """

    # insert :: macro.py_db_read(model)
    # macro :: py_sql_read :: {"single_model": "model_name_snake_case"}
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    result = cursor.execute(f"SELECT * FROM single_model WHERE id=?", (id,))
    entry = result.fetchone()
    if entry is None:
        raise NotFoundError(f'single_model {id} not found')
    # end macro ::
    
    return SingleModel(
        id=str(entry[0]),
        # insert :: macro.py_sql_convert(model.fields)
        # macro :: py_sql_convert_bool :: {"entry[1]": "local_var", "single_bool": "field_name"}
        single_bool=bool(entry[1]),
        # macro :: py_sql_convert_datetime :: {"entry[2]": "local_var", "single_datetime": "field_name"}
        single_datetime=datetime.strptime(entry[2], datetime_format_str).replace(microsecond=0),
        # macro :: py_sql_convert_str_enum :: {"entry[3]": "local_var", "single_enum": "field_name"}
        single_enum=entry[3],
        # macro :: py_sql_convert_float :: {"entry[4]": "local_var", "single_float": "field_name"}
        single_float=entry[4],
        # macro :: py_sql_convert_int :: {"entry[5]": "local_var", "single_int": "field_name"}
        single_int=entry[5],
        # macro :: py_sql_convert_str :: {"entry[6]": "local_var", "single_string": "field_name"}
        single_string=entry[6],
        # end macro ::
    ).validate()

def db_update_single_model(ctx:dict, obj:SingleModel) -> SingleModel:
    """
    update a single model in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the SingleModel object to update.

    return :: the SingleModel object.
    raises :: NotFoundError if the item is not found
    """
    if obj.id is None:
        raise ValueError('id must not be null to update an item')
    
    obj.validate()
    cursor:sqlite3.Cursor = ctx['db']['cursor']

    # insert :: macro.py_db_update(model)
    # macro :: py_sql_update :: {"single_model": "model_name_snake_case", "'single_bool'=?, 'single_datetime'=?, 'single_enum'=?, 'single_float'=?, 'single_int'=?, 'single_string'=?": "fields_sql", "obj.single_bool, obj.single_datetime.isoformat(), obj.single_enum, obj.single_float, obj.single_int, obj.single_string": "fields_py"}
    result = cursor.execute(
        "UPDATE single_model SET 'single_bool'=?, 'single_datetime'=?, 'single_enum'=?, 'single_float'=?, 'single_int'=?, 'single_string'=? WHERE id=?",
        (obj.single_bool, obj.single_datetime.isoformat(), obj.single_enum, obj.single_float, obj.single_int, obj.single_string, obj.id)
    )
    if result.rowcount == 0:
        raise NotFoundError(f'single_model {obj.id} not found')
    # end macro ::

    ctx['db']['commit']()
    return obj

def db_delete_single_model(ctx:dict, id:str) -> None:
    """
    delete a single model from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to delete.
    
    return :: None
    """

    cursor:sqlite3.Cursor = ctx['db']['cursor']
    # insert :: macro.py_db_delete(model)
    # macro :: py_sql_delete :: {"single_model": "model_name_snake_case"}
    cursor.execute(f"DELETE FROM single_model WHERE id=?", (id,))
    # end macro ::

    ctx['db']['commit']()

def db_list_single_model(ctx:dict, offset:int=0, limit:int=25) -> list[SingleModel]:
    """
    list single models from the database, and verify each

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.
    
    return :: list of each item as a dict.
    """
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    
    items = []
    query = cursor.execute("SELECT * FROM single_model ORDER BY id LIMIT ? OFFSET ?", (limit, offset))

    for entry in query.fetchall():
        # insert :: macro.py_db_list_lists(model)
        
        items.append(SingleModel(
            id=str(entry[0]),
            # replace :: macro.py_sql_convert(model.fields)
			single_bool=bool(entry[1]),
			single_datetime=entry[2],
			single_enum=entry[3],
			single_float=entry[4],
			single_int=entry[5],
			single_string=entry[6],
            # end replace ::
        ).validate())

    return items
