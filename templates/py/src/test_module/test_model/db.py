import sqlite3
from datetime import datetime
from core.types import datetime_format_str
from core.exceptions import NotFoundError
from test_module.test_model.model import TestModel

# vars :: {"test_module": "module.name.snake_case", "test_model": "model.name.snake_case", "TestModel": "model.name.pascal_case"}

__all__ = [
    'db_create_test_model', 
    'db_read_test_model',
    'db_update_test_model', 
    'db_delete_test_model', 
    'db_list_test_model',
]

def db_create_test_model(ctx:dict, obj:TestModel) -> TestModel:
    """
    create a test model in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the TestModel object to create.

    return :: and TestModel object with the new id.
    """
    if obj.id is not None:
        raise ValueError('id must be null to create a new item')
    
    obj.validate()
    cursor:sqlite3.Cursor = ctx['db']['cursor']

    # insert :: macro.py_db_create(model)
    # macro :: py_sql_create :: {"test_model": "model_name_snake_case", "('single_bool', 'single_datetime', 'single_enum', 'single_float', 'single_int', 'single_string')": "fields_sql", "VALUES(?, ?, ?, ?, ?, ?)": "sql_values", "obj.single_bool, obj.single_datetime.isoformat(), obj.single_enum, obj.single_float, obj.single_int, obj.single_string": "fields_py"}
    result = cursor.execute(
        "INSERT INTO test_model('single_bool', 'single_datetime', 'single_enum', 'single_float', 'single_int', 'single_string') VALUES(?, ?, ?, ?, ?, ?)",
        (obj.single_bool, obj.single_datetime.isoformat(), obj.single_enum, obj.single_float, obj.single_int, obj.single_string)
    )
    assert result.rowcount == 1
    assert result.lastrowid is not None
    obj.id = str(result.lastrowid)
    # macro :: py_sql_create_list_bool :: {"test_model": "model_name_snake_case", "multi_bool": "field_name"}
    _result = cursor.executemany(
        "INSERT INTO test_model_multi_bool(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_bool))
    )
    # macro :: py_sql_create_list_int :: {"test_model": "model_name_snake_case", "multi_int": "field_name"}
    _result = cursor.executemany(
        "INSERT INTO test_model_multi_int(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_int))
    )
    # macro :: py_sql_create_list_float :: {"test_model": "model_name_snake_case", "multi_float": "field_name"}
    _result = cursor.executemany(
        "INSERT INTO test_model_multi_float(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_float))
    )
    # macro :: py_sql_create_list_str :: {"test_model": "model_name_snake_case", "multi_string": "field_name"}
    _result = cursor.executemany(
        "INSERT INTO test_model_multi_string(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_string))
    )

    # macro :: py_sql_create_list_str_enum :: {"test_model": "model_name_snake_case", "multi_enum": "field_name"}
    _result = cursor.executemany(
        "INSERT INTO test_model_multi_enum(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_enum))
    )
    
    # macro :: py_sql_create_list_datetime :: {"test_model": "model_name_snake_case", "multi_datetime": "field_name"}
    _result = cursor.executemany(
        "INSERT INTO test_model_multi_datetime(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value.isoformat(), position, result.lastrowid) for position, value in enumerate(obj.multi_datetime))
    )
    # end macro ::

    ctx['db']['commit']()
    return obj

def db_read_test_model(ctx:dict, id:str) -> TestModel:
    """
    read a test model from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to read.
    
    return :: the TestModel object.
    raises :: NotFoundError if the item is not found.
    """

    # insert :: macro.py_db_read(model)
    # macro :: py_sql_read :: {"test_model": "model_name_snake_case"}
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    result = cursor.execute(f"SELECT * FROM test_model WHERE id=?", (id,))
    entry = result.fetchone()
    if entry is None:
        raise NotFoundError(f'test model {id} not found')
    # macro :: py_sql_read_list_bool :: {"test_model": "model_name_snake_case", "multi_bool": "field_name"}
    multi_bool_cursor = cursor.execute(f"SELECT value FROM test_model_multi_bool WHERE test_model_id=? ORDER BY position", (id,))
    multi_bool = [bool(row[0]) for row in multi_bool_cursor.fetchall()]
    # macro :: py_sql_read_list_int :: {"test_model": "model_name_snake_case", "multi_int": "field_name"}
    multi_int_cursor = cursor.execute(f"SELECT value FROM test_model_multi_int WHERE test_model_id=? ORDER BY position", (id,))
    multi_int = [row[0] for row in multi_int_cursor.fetchall()]
    # macro :: py_sql_read_list_float :: {"test_model": "model_name_snake_case", "multi_float": "field_name"}
    multi_float_cursor = cursor.execute(f"SELECT value FROM test_model_multi_float WHERE test_model_id=? ORDER BY position", (id,))
    multi_float = [row[0] for row in multi_float_cursor.fetchall()]
    # macro :: py_sql_read_list_str :: {"test_model": "model_name_snake_case", "multi_string": "field_name"}
    multi_string_cursor = cursor.execute(f"SELECT value FROM test_model_multi_string WHERE test_model_id=? ORDER BY position", (id,))
    multi_string = [row[0] for row in multi_string_cursor.fetchall()]
    # macro :: py_sql_read_list_str_enum :: {"test_model": "model_name_snake_case", "multi_enum": "field_name"}
    multi_enum_cursor = cursor.execute(f"SELECT value FROM test_model_multi_enum WHERE test_model_id=? ORDER BY position", (id,))
    multi_enum = [row[0] for row in multi_enum_cursor.fetchall()]
    # macro :: py_sql_read_list_datetime :: {"test_model": "model_name_snake_case", "multi_datetime": "field_name"}
    multi_datetime_cursor = cursor.execute(f"SELECT value FROM test_model_multi_datetime WHERE test_model_id=? ORDER BY position", (id,))
    multi_datetime = [
        datetime.strptime(row[0], datetime_format_str).replace(microsecond=0) 
        for row in multi_datetime_cursor.fetchall()
    ]
    # end macro ::
    
    return TestModel(
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
        # ignore ::
        multi_bool=multi_bool,
        multi_float=multi_float,
        multi_int=multi_int,
        multi_string=multi_string,
        multi_enum=multi_enum,
        multi_datetime=multi_datetime,
        # end ignore ::
    ).validate()

def db_update_test_model(ctx:dict, obj:TestModel) -> TestModel:
    """
    update a test model in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the TestModel object to update.

    return :: the TestModel object.
    raises :: NotFoundError if the item is not found
    """
    if obj.id is None:
        raise ValueError('id must not be null to update an item')
    
    obj.validate()
    cursor:sqlite3.Cursor = ctx['db']['cursor']

    # insert :: macro.py_db_update(model)
    # macro :: py_sql_update :: {"test_model": "model_name_snake_case", "'single_bool'=?, 'single_datetime'=?, 'single_enum'=?, 'single_float'=?, 'single_int'=?, 'single_string'=?": "fields_sql", "obj.single_bool, obj.single_datetime.isoformat(), obj.single_enum, obj.single_float, obj.single_int, obj.single_string": "fields_py"}
    result = cursor.execute(
        "UPDATE test_model SET 'single_bool'=?, 'single_datetime'=?, 'single_enum'=?, 'single_float'=?, 'single_int'=?, 'single_string'=? WHERE id=?",
        (obj.single_bool, obj.single_datetime.isoformat(), obj.single_enum, obj.single_float, obj.single_int, obj.single_string, obj.id)
    )
    if result.rowcount == 0:
        raise NotFoundError(f'test_model {obj.id} not found')
    # macro :: py_sql_update_list_bool :: {"test_model": "model_name_snake_case", "multi_bool": "field_name"}
    cursor.execute(f"DELETE FROM test_model_multi_bool WHERE test_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO test_model_multi_bool(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_bool))
    )
    # macro :: py_sql_update_list_float :: {"test_model": "model_name_snake_case", "multi_float": "field_name"}
    cursor.execute(f"DELETE FROM test_model_multi_float WHERE test_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO test_model_multi_float(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_float))
    )
    # macro :: py_sql_update_list_int :: {"test_model": "model_name_snake_case", "multi_int": "field_name"}
    cursor.execute(f"DELETE FROM test_model_multi_int WHERE test_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO test_model_multi_int(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_int))
    )
    # macro :: py_sql_update_list_str :: {"test_model": "model_name_snake_case", "multi_string": "field_name"}
    cursor.execute(f"DELETE FROM test_model_multi_string WHERE test_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO test_model_multi_string(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_string))
    )
    # macro :: py_sql_update_list_str_enum :: {"test_model": "model_name_snake_case", "multi_enum": "field_name"}
    cursor.execute(f"DELETE FROM test_model_multi_enum WHERE test_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO test_model_multi_enum(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_enum))
    )
    # macro :: py_sql_update_list_datetime :: {"test_model": "model_name_snake_case", "multi_datetime": "field_name"}
    cursor.execute(f"DELETE FROM test_model_multi_datetime WHERE test_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO test_model_multi_datetime(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value.isoformat(), position, obj.id) for position, value in enumerate(obj.multi_datetime))
    )
    # end macro ::
    ctx['db']['commit']()
    return obj

def db_delete_test_model(ctx:dict, id:str) -> None:
    """
    delete a test model from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to delete.
    
    return :: None
    """

    cursor:sqlite3.Cursor = ctx['db']['cursor']
    # insert :: macro.py_db_delete(model)
    # macro :: py_sql_delete :: {"test_model": "model_name_snake_case"}
    cursor.execute(f"DELETE FROM test_model WHERE id=?", (id,))
    # macro :: py_sql_delete_list :: {"test_model": "model_name_snake_case", "multi_bool": "field_name"}
    cursor.execute(f"DELETE FROM test_model_multi_bool WHERE test_model_id=?", (id,))
    # end macro ::
    # ignore ::
    cursor.execute(f"DELETE FROM test_model_multi_int WHERE test_model_id=?", (id,))
    cursor.execute(f"DELETE FROM test_model_multi_float WHERE test_model_id=?", (id,))
    cursor.execute(f"DELETE FROM test_model_multi_string WHERE test_model_id=?", (id,))
    cursor.execute(f"DELETE FROM test_model_multi_enum WHERE test_model_id=?", (id,))
    cursor.execute(f"DELETE FROM test_model_multi_datetime WHERE test_model_id=?", (id,))
    # end ignore ::

    ctx['db']['commit']()

def db_list_test_model(ctx:dict, offset:int=0, limit:int=25) -> list[TestModel]:
    """
    list test models from the database, and verify each

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.
    
    return :: list of each item as a dict.
    """
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    
    items = []
    query = cursor.execute("SELECT * FROM test_model ORDER BY id LIMIT ? OFFSET ?", (limit, offset))

    for entry in query.fetchall():
        # insert :: macro.py_db_list_lists(model)
        # macro :: py_sql_list_bool :: {"test_model": "model_name_snake_case", "multi_bool": "field_name"}
        multi_bool_cursor = cursor.execute(f"SELECT value FROM test_model_multi_bool WHERE test_model_id=? ORDER BY position", (entry[0],))
        multi_bool = [bool(row[0]) for row in multi_bool_cursor.fetchall()]
        # macro :: py_sql_list_int :: {"test_model": "model_name_snake_case", "multi_int": "field_name"}
        multi_int_cursor = cursor.execute(f"SELECT value FROM test_model_multi_int WHERE test_model_id=? ORDER BY position", (entry[0],))
        multi_int = [row[0] for row in multi_int_cursor.fetchall()]
        # macro :: py_sql_list_float :: {"test_model": "model_name_snake_case", "multi_float": "field_name"}
        multi_float_cursor = cursor.execute(f"SELECT value FROM test_model_multi_float WHERE test_model_id=? ORDER BY position", (entry[0],))
        multi_float = [row[0] for row in multi_float_cursor.fetchall()]
        # macro :: py_sql_list_str :: {"test_model": "model_name_snake_case", "multi_string": "field_name"}
        multi_string_cursor = cursor.execute(f"SELECT value FROM test_model_multi_string WHERE test_model_id=? ORDER BY position", (entry[0],))
        multi_string = [row[0] for row in multi_string_cursor.fetchall()]
        # macro :: py_sql_list_str_enum :: {"test_model": "model_name_snake_case", "multi_enum": "field_name"}
        multi_enum_cursor = cursor.execute(f"SELECT value FROM test_model_multi_enum WHERE test_model_id=? ORDER BY position", (entry[0],))
        multi_enum = [row[0] for row in multi_enum_cursor.fetchall()]
        # macro :: py_sql_list_datetime :: {"test_model": "model_name_snake_case", "multi_datetime": "field_name"}
        multi_datetime_cursor = cursor.execute(f"SELECT value FROM test_model_multi_datetime WHERE test_model_id=? ORDER BY position", (entry[0],))
        multi_datetime = [
            datetime.strptime(row[0], datetime_format_str).replace(microsecond=0) 
            for row in multi_datetime_cursor.fetchall()
        ]
        
        # end macro ::
        items.append(TestModel(
            id=str(entry[0]),
            # replace :: macro.py_sql_convert(model.fields)
			multi_bool=multi_bool,
			multi_float=multi_float,
			multi_int=multi_int,
			multi_string=multi_string,
            multi_enum=multi_enum,
            multi_datetime=multi_datetime,
			single_bool=bool(entry[1]),
			single_datetime=entry[2],
			single_enum=entry[3],
			single_float=entry[4],
			single_int=entry[5],
			single_string=entry[6],
            # end replace ::
        ).validate())

    return items