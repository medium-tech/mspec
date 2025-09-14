import sqlite3
from datetime import datetime
from core.types import datetime_format_str
from core.exceptions import ForbiddenError, NotFoundError
from template_module.multi_model.model import MultiModel

__all__ = [
    'db_create_multi_model', 
    'db_read_multi_model',
    'db_update_multi_model', 
    'db_delete_multi_model', 
    'db_list_multi_model',
]

def db_create_multi_model(ctx:dict, obj:MultiModel) -> MultiModel:
    """
    create a multi model in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the MultiModel object to create.

    return :: and MultiModel object with the new id.
    """
    if obj.id is not None:
        raise ValueError('id must be null to create a new item')
    
    obj.validate()
    cursor:sqlite3.Cursor = ctx['db']['cursor']

    # macro :: py_create_model_login_check :: {"multi model": "model_name_lower_case"}
    # must be logged in to make multi model
    user = ctx['auth']['get_user']()
    obj.user_id = user.id
    assert obj.user_id is not None
    # end macro ::

    # macro :: py_create_model_max_created_check :: {"1": "max_models_per_user", "multi_model": "model_name_snake_case"}
    # each user can only create a maximum of 1 multi_model(s)
    cursor.execute("SELECT COUNT(*) FROM multi_model WHERE user_id=?", (user.id,))
    count = cursor.fetchone()[0]
    if count >= 1:
        raise ValueError('user has reached the maximum number of multi_model(s)')
    # end macro ::

    result = cursor.execute(
        "INSERT INTO multi_model('user_id') VALUES(?)",
        (user.id,)
    )
    assert result.rowcount == 1
    assert result.lastrowid is not None
    obj.id = str(result.lastrowid)
    
    # macro :: py_sql_create_list_bool :: {"multi_model": "model_name_snake_case", "multi_bool": "field_name"}
    cursor.executemany(
        "INSERT INTO multi_model_multi_bool(value, position, multi_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_bool))
    )
    # macro :: py_sql_create_list_int :: {"multi_model": "model_name_snake_case", "multi_int": "field_name"}
    cursor.executemany(
        "INSERT INTO multi_model_multi_int(value, position, multi_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_int))
    )
    # macro :: py_sql_create_list_float :: {"multi_model": "model_name_snake_case", "multi_float": "field_name"}
    cursor.executemany(
        "INSERT INTO multi_model_multi_float(value, position, multi_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_float))
    )
    # macro :: py_sql_create_list_str :: {"multi_model": "model_name_snake_case", "multi_string": "field_name"}
    cursor.executemany(
        "INSERT INTO multi_model_multi_string(value, position, multi_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_string))
    )

    # macro :: py_sql_create_list_str_enum :: {"multi_model": "model_name_snake_case", "multi_enum": "field_name"}
    cursor.executemany(
        "INSERT INTO multi_model_multi_enum(value, position, multi_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_enum))
    )

    # macro :: py_sql_create_list_datetime :: {"multi_model": "model_name_snake_case", "multi_datetime": "field_name"}
    cursor.executemany(
        "INSERT INTO multi_model_multi_datetime(value, position, multi_model_id) VALUES(?, ?, ?)",
        ((value.isoformat(), position, result.lastrowid) for position, value in enumerate(obj.multi_datetime))
    )
    # end macro ::

    ctx['db']['commit']()
    return obj

def db_read_multi_model(ctx:dict, id:str) -> MultiModel:
    """
    read a multi model from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to read.

    return :: the MultiModel object.
    raises :: NotFoundError if the item is not found.
    """

    cursor:sqlite3.Cursor = ctx['db']['cursor']
    result = cursor.execute(f"SELECT * FROM multi_model WHERE id=?", (id,))
    entry = result.fetchone()
    if entry is None:
        raise NotFoundError(f'multi model {id} not found')
    # macro :: py_sql_read_list_bool :: {"multi_model": "model_name_snake_case", "multi_bool": "field_name"}
    multi_bool_cursor = cursor.execute(f"SELECT value FROM multi_model_multi_bool WHERE multi_model_id=? ORDER BY position", (id,))
    multi_bool = [bool(row[0]) for row in multi_bool_cursor.fetchall()]
    # macro :: py_sql_read_list_int :: {"multi_model": "model_name_snake_case", "multi_int": "field_name"}
    multi_int_cursor = cursor.execute(f"SELECT value FROM multi_model_multi_int WHERE multi_model_id=? ORDER BY position", (id,))
    multi_int = [row[0] for row in multi_int_cursor.fetchall()]
    # macro :: py_sql_read_list_float :: {"multi_model": "model_name_snake_case", "multi_float": "field_name"}
    multi_float_cursor = cursor.execute(f"SELECT value FROM multi_model_multi_float WHERE multi_model_id=? ORDER BY position", (id,))
    multi_float = [row[0] for row in multi_float_cursor.fetchall()]
    # macro :: py_sql_read_list_str :: {"multi_model": "model_name_snake_case", "multi_string": "field_name"}
    multi_string_cursor = cursor.execute(f"SELECT value FROM multi_model_multi_string WHERE multi_model_id=? ORDER BY position", (id,))
    multi_string = [row[0] for row in multi_string_cursor.fetchall()]
    # macro :: py_sql_read_list_str_enum :: {"multi_model": "model_name_snake_case", "multi_enum": "field_name"}
    multi_enum_cursor = cursor.execute(f"SELECT value FROM multi_model_multi_enum WHERE multi_model_id=? ORDER BY position", (id,))
    multi_enum = [row[0] for row in multi_enum_cursor.fetchall()]
    # macro :: py_sql_read_list_datetime :: {"multi_model": "model_name_snake_case", "multi_datetime": "field_name"}
    multi_datetime_cursor = cursor.execute(f"SELECT value FROM multi_model_multi_datetime WHERE multi_model_id=? ORDER BY position", (id,))
    multi_datetime = [
        datetime.strptime(row[0], datetime_format_str).replace(microsecond=0) 
        for row in multi_datetime_cursor.fetchall()
    ]
    # end macro ::

    return MultiModel(
        id=str(entry[0]),
        user_id=str(entry[1]),
        multi_bool=multi_bool,
        multi_float=multi_float,
        multi_int=multi_int,
        multi_string=multi_string,
        multi_enum=multi_enum,
        multi_datetime=multi_datetime
    ).validate()

def db_update_multi_model(ctx:dict, obj:MultiModel) -> MultiModel:
    """
    update a multi model in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the MultiModel object to update.

    return :: the MultiModel object.
    raises :: NotFoundError if the item is not found
    """
    if obj.id is None:
        raise ValueError('id must not be null to update an item')
    
    obj.validate()

    # macro :: py_db_update_auth :: {"multi_model": "model.name.snake_case"}
    user = ctx['auth']['get_user']()
    if obj.user_id != user.id:
        raise ForbiddenError('not allowed to update this multi_model')
    # end macro ::

    cursor:sqlite3.Cursor = ctx['db']['cursor']

    # macro :: py_sql_update_list_bool :: {"multi_model": "model_name_snake_case", "multi_bool": "field_name"}
    cursor.execute(f"DELETE FROM multi_model_multi_bool WHERE multi_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO multi_model_multi_bool(value, position, multi_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_bool))
    )
    # macro :: py_sql_update_list_float :: {"multi_model": "model_name_snake_case", "multi_float": "field_name"}
    cursor.execute(f"DELETE FROM multi_model_multi_float WHERE multi_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO multi_model_multi_float(value, position, multi_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_float))
    )
    # macro :: py_sql_update_list_int :: {"multi_model": "model_name_snake_case", "multi_int": "field_name"}
    cursor.execute(f"DELETE FROM multi_model_multi_int WHERE multi_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO multi_model_multi_int(value, position, multi_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_int))
    )
    # macro :: py_sql_update_list_str :: {"multi_model": "model_name_snake_case", "multi_string": "field_name"}
    cursor.execute(f"DELETE FROM multi_model_multi_string WHERE multi_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO multi_model_multi_string(value, position, multi_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_string))
    )
    # macro :: py_sql_update_list_str_enum :: {"multi_model": "model_name_snake_case", "multi_enum": "field_name"}
    cursor.execute(f"DELETE FROM multi_model_multi_enum WHERE multi_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO multi_model_multi_enum(value, position, multi_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_enum))
    )
    # macro :: py_sql_update_list_datetime :: {"multi_model": "model_name_snake_case", "multi_datetime": "field_name"}
    cursor.execute(f"DELETE FROM multi_model_multi_datetime WHERE multi_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO multi_model_multi_datetime(value, position, multi_model_id) VALUES(?, ?, ?)",
        ((value.isoformat(), position, obj.id) for position, value in enumerate(obj.multi_datetime))
    )
    # end macro ::
    ctx['db']['commit']()
    return obj

def db_delete_multi_model(ctx:dict, id:str) -> None:
    """
    delete a multi model from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to delete.
    
    return :: None
    """

    cursor:sqlite3.Cursor = ctx['db']['cursor']

    # macro :: py_db_delete_auth :: {"multi_model": "model.name.snake_case"}
    user = ctx['auth']['get_user']()
    try:
        obj = db_read_multi_model(ctx, id)
    except NotFoundError:
        return

    if obj.user_id != user.id:
        raise ForbiddenError('not allowed to delete this multi_model')
    # end macro ::

    cursor.execute(f"DELETE FROM multi_model WHERE id=?", (id,))
    # macro :: py_sql_delete_list :: {"multi_model": "model_name_snake_case", "multi_bool": "field_name"}
    cursor.execute(f"DELETE FROM multi_model_multi_bool WHERE multi_model_id=?", (id,))
    # end macro ::

    cursor.execute(f"DELETE FROM multi_model_multi_int WHERE multi_model_id=?", (id,))
    cursor.execute(f"DELETE FROM multi_model_multi_float WHERE multi_model_id=?", (id,))
    cursor.execute(f"DELETE FROM multi_model_multi_string WHERE multi_model_id=?", (id,))
    cursor.execute(f"DELETE FROM multi_model_multi_enum WHERE multi_model_id=?", (id,))
    cursor.execute(f"DELETE FROM multi_model_multi_datetime WHERE multi_model_id=?", (id,))

    ctx['db']['commit']()

def db_list_multi_model(ctx:dict, offset:int=0, limit:int=25) -> dict:
    """
    list multi models from the database, and verify each

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.

    return :: dict with two keys:
        total :: int of the total number of items.
        items :: list of each item as a dict.
    """
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    
    items = []
    query = cursor.execute("SELECT * FROM multi_model ORDER BY id LIMIT ? OFFSET ?", (limit, offset))

    for entry in query.fetchall():
        # macro :: py_sql_list_bool :: {"multi_model": "model_name_snake_case", "multi_bool": "field_name"}
        multi_bool_cursor = cursor.execute(f"SELECT value FROM multi_model_multi_bool WHERE multi_model_id=? ORDER BY position", (entry[0],))
        multi_bool = [bool(row[0]) for row in multi_bool_cursor.fetchall()]
        # macro :: py_sql_list_int :: {"multi_model": "model_name_snake_case", "multi_int": "field_name"}
        multi_int_cursor = cursor.execute(f"SELECT value FROM multi_model_multi_int WHERE multi_model_id=? ORDER BY position", (entry[0],))
        multi_int = [row[0] for row in multi_int_cursor.fetchall()]
        # macro :: py_sql_list_float :: {"multi_model": "model_name_snake_case", "multi_float": "field_name"}
        multi_float_cursor = cursor.execute(f"SELECT value FROM multi_model_multi_float WHERE multi_model_id=? ORDER BY position", (entry[0],))
        multi_float = [row[0] for row in multi_float_cursor.fetchall()]
        # macro :: py_sql_list_str :: {"multi_model": "model_name_snake_case", "multi_string": "field_name"}
        multi_string_cursor = cursor.execute(f"SELECT value FROM multi_model_multi_string WHERE multi_model_id=? ORDER BY position", (entry[0],))
        multi_string = [row[0] for row in multi_string_cursor.fetchall()]
        # macro :: py_sql_list_str_enum :: {"multi_model": "model_name_snake_case", "multi_enum": "field_name"}
        multi_enum_cursor = cursor.execute(f"SELECT value FROM multi_model_multi_enum WHERE multi_model_id=? ORDER BY position", (entry[0],))
        multi_enum = [row[0] for row in multi_enum_cursor.fetchall()]
        # macro :: py_sql_list_datetime :: {"multi_model": "model_name_snake_case", "multi_datetime": "field_name"}
        multi_datetime_cursor = cursor.execute(f"SELECT value FROM multi_model_multi_datetime WHERE multi_model_id=? ORDER BY position", (entry[0],))
        multi_datetime = [
            datetime.strptime(row[0], datetime_format_str).replace(microsecond=0) 
            for row in multi_datetime_cursor.fetchall()
        ]
        # end macro ::

        items.append(MultiModel(
            id=str(entry[0]),
            user_id=str(entry[1]),
			multi_bool=multi_bool,
			multi_float=multi_float,
			multi_int=multi_int,
			multi_string=multi_string,
            multi_enum=multi_enum,
            multi_datetime=multi_datetime,
        ).validate())

    return {
        'total': cursor.execute("SELECT COUNT(*) FROM multi_model").fetchone()[0],
        'items': items
    }