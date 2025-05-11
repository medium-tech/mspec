from core.exceptions import NotFoundError

from test_module.test_model.model import TestModel

import sqlite3

# vars :: {"test_module": "module.name.snake_case", "test_model": "model.name.snake_case", "TestModel": "model.name.pascal_case", "unit_test": "project.name.snake_case"}

__all__ = [
    'db_create_test_model', 
    'db_read_test_model',
    'db_update_test_model', 
    'db_delete_test_model', 
    'db_list_test_model',
]

def db_create_test_model(ctx:dict, obj:TestModel) -> TestModel:
    """
    create a example item in the database, verifying the data first.

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
    result = cursor.execute(
        "INSERT INTO test_model('single_bool', 'single_datetime', 'single_enum', 'single_float', 'single_int', 'single_string') VALUES(?, ?, ?, ?, ?, ?)",
        (obj.single_bool, obj.single_datetime.isoformat(), obj.single_enum, obj.single_float, obj.single_int, obj.single_string,)
    )
    assert result.rowcount == 1
    assert result.lastrowid is not None
    obj.id = str(result.lastrowid)

    result = cursor.executemany(
        "INSERT INTO test_model_multi_bool(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_bool))
    )

    result = cursor.executemany(
        "INSERT INTO test_model_multi_int(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_int))
    )

    result = cursor.executemany(
        "INSERT INTO test_model_multi_float(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_float))
    )

    result = cursor.executemany(
        "INSERT INTO test_model_multi_string(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, result.lastrowid) for position, value in enumerate(obj.multi_string))
    )


    # macro :: py_sql_create :: {"test_model": "model_name_snake_case", "('description', 'verified', 'color', 'count', 'score', 'when')": "fields_sql", "VALUES(?, ?, ?, ?, ?, ?)": "sql_values", "obj.description, obj.verified, obj.color, obj.count, obj.score, obj.when.isoformat()": "fields_py"}
    # macro :: py_sql_create_list :: {"test_model": "model_name_snake_case", "stuff": "field_name"}
    # end macro ::
    
    ctx['db']['commit']()
    return obj

def db_read_test_model(ctx:dict, id:str) -> TestModel:
    """
    read a example item from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to read.
    
    return :: the TestModel object.
    raises :: NotFoundError if the item is not found.
    """

    # insert :: macro.py_db_read(model)
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    result = cursor.execute(f"SELECT * FROM test_model WHERE id=?", (id,))
    entry = result.fetchone()
    if entry is None:
        raise NotFoundError(f'example item {id} not found')

    multi_bool_cursor = cursor.execute(f"SELECT value FROM test_model_multi_bool WHERE test_model_id=? ORDER BY position", (id,))
    multi_bool = [bool(row[0]) for row in multi_bool_cursor.fetchall()]

    multi_int_cursor = cursor.execute(f"SELECT value FROM test_model_multi_int WHERE test_model_id=? ORDER BY position", (id,))
    multi_int = [row[0] for row in multi_int_cursor.fetchall()]

    multi_float_cursor = cursor.execute(f"SELECT value FROM test_model_multi_float WHERE test_model_id=? ORDER BY position", (id,))
    multi_float = [row[0] for row in multi_float_cursor.fetchall()]

    multi_string_cursor = cursor.execute(f"SELECT value FROM test_model_multi_string WHERE test_model_id=? ORDER BY position", (id,))
    multi_string = [row[0] for row in multi_string_cursor.fetchall()]


    # macro :: py_sql_read :: {"test_model": "model_name_snake_case"}
    # macro :: py_sql_read_list :: {"test_model": "model_name_snake_case", "stuff": "field_name", "row[0]": "item"}
    # end macro ::
    
    return TestModel(
        id=str(entry[0]),
        # replace :: macro.py_sql_convert(model.fields)
        # end replace ::
			multi_bool=multi_bool,
			multi_float=multi_float,
			multi_int=multi_int,
			multi_string=multi_string,
			single_bool=bool(entry[1]),
			single_datetime=entry[2],
			single_enum=entry[3],
			single_float=entry[4],
			single_int=entry[5],
			single_string=entry[6],

    ).validate()

def db_update_test_model(ctx:dict, obj:TestModel) -> TestModel:
    """
    update a example item in the database, and verify the data first.

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
    result = cursor.execute(
        "UPDATE test_model SET 'single_bool'=?, 'single_datetime'=?, 'single_enum'=?, 'single_float'=?, 'single_int'=?, 'single_string'=? WHERE id=?",
        (obj.single_bool, obj.single_datetime.isoformat(), obj.single_enum, obj.single_float, obj.single_int, obj.single_string, obj.id)
    )
    if result.rowcount == 0:
        raise NotFoundError(f'example item {obj.id} not found')

    cursor.execute(f"DELETE FROM test_model_multi_bool WHERE test_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO test_model_multi_bool(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_bool))
    )

    cursor.execute(f"DELETE FROM test_model_multi_float WHERE test_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO test_model_multi_float(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_float))
    )

    cursor.execute(f"DELETE FROM test_model_multi_int WHERE test_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO test_model_multi_int(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_int))
    )

    cursor.execute(f"DELETE FROM test_model_multi_string WHERE test_model_id=?", (obj.id,))
    cursor.executemany(
        "INSERT INTO test_model_multi_string(value, position, test_model_id) VALUES(?, ?, ?)",
        ((value, position, obj.id) for position, value in enumerate(obj.multi_string))
    )


    # macro :: py_sql_update :: {"test_model": "model_name_snake_case", "'description'=?, 'verified'=?, 'color'=?, 'count'=?, 'score'=?, 'when'=?": "fields_sql", "obj.description, obj.verified, obj.color, obj.count, obj.score, obj.when.isoformat()": "fields_py"}
    # macro :: py_sql_update_list :: {"test_model": "model_name_snake_case", "stuff": "field_name"}
    # end macro ::
    ctx['db']['commit']()
    return obj

def db_delete_test_model(ctx:dict, id:str) -> None:
    """
    delete a example item from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the item to delete.
    
    return :: None
    """

    cursor:sqlite3.Cursor = ctx['db']['cursor']
    # insert :: macro.py_db_delete(model)
    cursor.execute(f"DELETE FROM test_model WHERE id=?", (id,))

    cursor.execute(f"DELETE FROM test_model_multi_bool WHERE test_model_id=?", (id,))

    cursor.execute(f"DELETE FROM test_model_multi_int WHERE test_model_id=?", (id,))

    cursor.execute(f"DELETE FROM test_model_multi_float WHERE test_model_id=?", (id,))

    cursor.execute(f"DELETE FROM test_model_multi_string WHERE test_model_id=?", (id,))


    # macro :: py_sql_delete :: {"test_model": "model_name_snake_case"}
    # macro :: py_sql_delete_list :: {"test_model": "model_name_snake_case", "stuff": "field_name"}
    # end macro ::
    ctx['db']['commit']()

def db_list_test_model(ctx:dict, offset:int=0, limit:int=25) -> list[TestModel]:
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
    query = cursor.execute("SELECT * FROM test_model ORDER BY id LIMIT ? OFFSET ?", (limit, offset))

    for entry in query.fetchall():
        # insert :: macro.py_db_list_lists(model)
        multi_bool_cursor = cursor.execute(f"SELECT value FROM test_model_multi_bool WHERE test_model_id=? ORDER BY position", (entry[0],))
        multi_bool = [bool(row[0]) for row in multi_bool_cursor.fetchall()]

        multi_int_cursor = cursor.execute(f"SELECT value FROM test_model_multi_int WHERE test_model_id=? ORDER BY position", (entry[0],))
        multi_int = [row[0] for row in multi_int_cursor.fetchall()]

        multi_float_cursor = cursor.execute(f"SELECT value FROM test_model_multi_float WHERE test_model_id=? ORDER BY position", (entry[0],))
        multi_float = [row[0] for row in multi_float_cursor.fetchall()]

        multi_string_cursor = cursor.execute(f"SELECT value FROM test_model_multi_string WHERE test_model_id=? ORDER BY position", (entry[0],))
        multi_string = [row[0] for row in multi_string_cursor.fetchall()]


        # macro :: py_sql_list_list :: {"test_model": "model_name_snake_case", "stuff": "field_name", "row[0]": "item"}
        # end macro ::
        items.append(TestModel(
            id=str(entry[0]),
            # replace :: macro.py_sql_convert(model.fields)
            # end replace ::
			multi_bool=multi_bool,
			multi_float=multi_float,
			multi_int=multi_int,
			multi_string=multi_string,
			single_bool=bool(entry[1]),
			single_datetime=entry[2],
			single_enum=entry[3],
			single_float=entry[4],
			single_int=entry[5],
			single_string=entry[6],

        ).validate())

    return items