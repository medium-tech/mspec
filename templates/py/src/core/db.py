import atexit
import os
import sqlite3
from pathlib import Path

from core.types import Meta
from core.models import *
from core.exceptions import NotFoundError, ForbiddenError

__all__ = [
    'MSPEC_DB_URL',
    'create_db_context',
    'create_db_tables',

    'db_create_user',
    'db_read_user',
    'db_update_user',
    'db_delete_user',
    'db_list_user',

    'db_create_user_password_hash',
    'db_read_user_password_hash',
    'db_update_user_password_hash',
    'db_delete_user_password_hash',
    'db_list_user_password_hash'
]

_default_db_path = Path(__file__).parent / 'db.sqlite3'

MSPEC_DB_URL = os.environ.get('MSPEC_DB_URL', f'file:{_default_db_path}')

def create_db_context() -> dict:
    """
    initialize the database client.
    
    return :: dict
    """

    connection = sqlite3.connect(MSPEC_DB_URL, uri=True)
    atexit.register(lambda: connection.close())

    return {
        'db': {
            'url': MSPEC_DB_URL,
            'connection': connection,
            'cursor': connection.cursor(),
            'commit': connection.commit
        }
    }

def create_db_tables(ctx:dict) -> None:
    """
    create the database tables if they do not exist.

    args ::
        ctx :: dict containing the database client
    """

    cursor:sqlite3.Cursor = ctx['db']['cursor']
    cursor.execute("CREATE TABLE IF NOT EXISTS user(id INTEGER PRIMARY KEY, name, email, profile)")
    cursor.execute("CREATE TABLE IF NOT EXISTS user_password_hash(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES user(id), hash)")

    # insert :: macro.py_create_tables(all_models)
    # macro :: py_create_model_table :: {"single_model": "model_name_snake_case", ", 'single_bool', 'single_datetime', 'single_enum', 'single_float', 'single_int', 'single_string'": "field_list"}
    #
    # single model
    #

    cursor.execute("CREATE TABLE IF NOT EXISTS single_model(id INTEGER PRIMARY KEY, 'single_bool', 'single_datetime', 'single_enum', 'single_float', 'single_int', 'single_string')")
    # end macro ::
    # macro :: py_create_model_table_list :: {"single_model": "model_name_snake_case", "multi_bool": "field_name"}
    cursor.execute("CREATE TABLE IF NOT EXISTS single_model_multi_bool(id INTEGER PRIMARY KEY, value, position, single_model_id INTEGER REFERENCES single_model(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS single_model_multi_bool_index ON single_model_multi_bool(single_model_id)')
    # end macro ::

    # ignore ::
    cursor.execute("CREATE TABLE IF NOT EXISTS single_model_multi_int(id INTEGER PRIMARY KEY, value, position, single_model_id INTEGER REFERENCES single_model(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS single_model_multi_int_index ON single_model_multi_int(single_model_id)')

    cursor.execute("CREATE TABLE IF NOT EXISTS single_model_multi_float(id INTEGER PRIMARY KEY, value, position, single_model_id INTEGER REFERENCES single_model(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS single_model_multi_float_index ON single_model_multi_float(single_model_id)')

    cursor.execute("CREATE TABLE IF NOT EXISTS single_model_multi_string(id INTEGER PRIMARY KEY, value, position, single_model_id INTEGER REFERENCES single_model(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS single_model_multi_string_index ON single_model_multi_string(single_model_id)')

    cursor.execute("CREATE TABLE IF NOT EXISTS single_model_multi_enum(id INTEGER PRIMARY KEY, value, position, single_model_id INTEGER REFERENCES single_model(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS single_model_multi_enum_index ON single_model_multi_enum(single_model_id)')

    cursor.execute("CREATE TABLE IF NOT EXISTS single_model_multi_datetime(id INTEGER PRIMARY KEY, value, position, single_model_id INTEGER REFERENCES single_model(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS single_model_multi_datetime_index ON single_model_multi_datetime(single_model_id)')

    # end ignore ::
    # ignore ::

    #
    # multi model
    #

    cursor.execute("CREATE TABLE IF NOT EXISTS multi_model(id INTEGER PRIMARY KEY, 'user_id')")
    # end ignore ::

    # macro :: py_create_model_table_list :: {"multi_model": "model_name_snake_case", "multi_bool": "field_name"}
    cursor.execute("CREATE TABLE IF NOT EXISTS multi_model_multi_bool(id INTEGER PRIMARY KEY, value, position, multi_model_id INTEGER REFERENCES multi_model(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS multi_model_multi_bool_index ON multi_model_multi_bool(multi_model_id)')
    # end macro ::

    # ignore ::
    cursor.execute("CREATE TABLE IF NOT EXISTS multi_model_multi_int(id INTEGER PRIMARY KEY, value, position, multi_model_id INTEGER REFERENCES multi_model(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS multi_model_multi_int_index ON multi_model_multi_int(multi_model_id)')

    cursor.execute("CREATE TABLE IF NOT EXISTS multi_model_multi_float(id INTEGER PRIMARY KEY, value, position, multi_model_id INTEGER REFERENCES multi_model(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS multi_model_multi_float_index ON multi_model_multi_float(multi_model_id)')

    cursor.execute("CREATE TABLE IF NOT EXISTS multi_model_multi_string(id INTEGER PRIMARY KEY, value, position, multi_model_id INTEGER REFERENCES multi_model(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS multi_model_multi_string_index ON multi_model_multi_string(multi_model_id)')

    cursor.execute("CREATE TABLE IF NOT EXISTS multi_model_multi_enum(id INTEGER PRIMARY KEY, value, position, multi_model_id INTEGER REFERENCES multi_model(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS multi_model_multi_enum_index ON multi_model_multi_enum(multi_model_id)')

    cursor.execute("CREATE TABLE IF NOT EXISTS multi_model_multi_datetime(id INTEGER PRIMARY KEY, value, position, multi_model_id INTEGER REFERENCES multi_model(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS multi_model_multi_datetime_index ON multi_model_multi_datetime(multi_model_id)')
    # end ignore ::

    ctx['db']['commit']()

#
# model crud ops
#

# user #

def db_create_user(ctx:dict, obj:User) -> User:
    """
    create a user in the database, verifying the data first.

    this should not be called directly, use auth.create_new_user which 
    will create a user and a password hash and verify the email is not in use.

    args ::
        ctx :: dict containing the database client
        obj :: the data to create the user with.

    return :: user object
    """
    if obj.id is not None:
        raise ValueError('cannot use user with id to create new user')
    
    obj.validate()
    
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    result = cursor.execute("INSERT INTO user(name, email) VALUES(?, ?)", (obj.name, obj.email))
    assert result.rowcount == 1

    ctx['db']['commit']()

    obj.id = str(result.lastrowid)
    return obj

def db_read_user(ctx:dict, id:str) -> User:
    """
    read a user from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the user to read.
    
    return :: user object
    raises :: NotFoundError if the user does not exist
    """

    cursor:sqlite3.Cursor = ctx['db']['cursor']
    db_entry = cursor.execute("SELECT * FROM user WHERE id = ?", (id,)).fetchone()
    if db_entry is None:
        raise NotFoundError(f'user {id} not found')
    else:
        return User(
            id=str(db_entry[0]),
            name=db_entry[1],
            email=db_entry[2]
        ).validate()

def db_update_user(ctx:dict, obj:User) -> User:
    """
    update a user in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the data to update the user with.

    return :: user object
    raises :: NotFoundError if the user does not exist
    """
    obj.validate()

    if obj.id is None:
        raise ValueError('cannot update user without id')
    
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    result = cursor.execute(
        "UPDATE user SET name = ?, email = ? WHERE id = ?",
        (obj.name, obj.email, obj.id)
    )
    if result.rowcount == 0:
        raise NotFoundError(f'user {obj.id} not found')
    
    ctx['db']['commit']()

    return obj

def db_delete_user(ctx:dict, id:str) -> None:
    """
    delete a user from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the user to delete.

    return :: None
    """

    cursor:sqlite3.Cursor = ctx['db']['cursor']
    cursor.execute("DELETE FROM user WHERE id = ?", (id,))
    cursor.execute("DELETE FROM user_password_hash WHERE user_id = ?", (id,))
    ctx['db']['commit']()

def db_list_user(ctx:dict, offset:int=0, limit:int=25) -> list[User]:
    """
    list users in the database.

    args ::
        ctx :: dict containing the database client

    return :: list of user objects
    """

    cursor:sqlite3.Cursor = ctx['db']['cursor']
    items = []
    for item in cursor.execute("SELECT * FROM user ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)):
        items.append(User(
            id=str(item[0]),
            name=item[1],
            email=item[2]
        ).validate())
    
    return items

# user password hash #

def db_create_user_password_hash(ctx:dict, pw_hash:UserPasswordHash) -> UserPasswordHash:
    raise ForbiddenError('user password hash is not creatable')

def db_read_user_password_hash(ctx:dict, id:str) -> dict:
    raise ForbiddenError('user password hash is not readable')
    
def db_update_user_password_hash(ctx:dict, pw_hash:UserPasswordHash) -> UserPasswordHash:
    raise ForbiddenError('user password hash is not updatable')

def db_delete_user_password_hash(ctx:dict, id:str) -> None:
    raise ForbiddenError('user password hash is not deletable')

def db_list_user_password_hash(ctx:dict, offset:int=0, limit:int=25) -> list[dict]:
    raise ForbiddenError('user password hash is not readable')
