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
    'db_list_user_password_hash',

    'db_create_profile',
    'db_read_profile',
    'db_update_profile',
    'db_delete_profile',
    'db_list_profile'
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
    cursor.execute("CREATE TABLE IF NOT EXISTS profile(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES user(id), name, bio)")
    cursor.execute("CREATE TABLE IF NOT EXISTS profile_meta_data(id INTEGER PRIMARY KEY, profile_id INTEGER REFERENCES profile(id), key, value_bool, value_int, value_float, value_str)")
    cursor.execute("CREATE TABLE IF NOT EXISTS profile_meta_tags(id INTEGER PRIMARY KEY, profile_id INTEGER REFERENCES profile(id), value, position)")
    cursor.execute("CREATE TABLE IF NOT EXISTS profile_meta_hierarchies(id INTEGER PRIMARY KEY, profile_id INTEGER REFERENCES profile(id), value, position)")

    # for :: {% for item in all_models %} :: {"example_item": "item.model.name.snake_case", "'description', 'verified', 'color', 'count', 'score', 'when'": "item.model.field_list"}
    cursor.execute("CREATE TABLE IF NOT EXISTS example_item(id INTEGER PRIMARY KEY, 'description', 'verified', 'color', 'count', 'score', 'when')")
    # end for ::
    cursor.execute("CREATE TABLE IF NOT EXISTS example_item_stuff(id INTEGER PRIMARY KEY, value, position, example_item_id INTEGER REFERENCES example_item(id))")
    cursor.execute('CREATE INDEX IF NOT EXISTS example_item_stuff_index ON example_item_stuff(example_item_id);')

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
    result = cursor.execute("INSERT INTO user(name, email, profile) VALUES(?, ?, ?)", (obj.name, obj.email, obj.profile))
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
            email=db_entry[2],
            profile=db_entry[3]
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
        "UPDATE user SET name = ?, email = ?, profile = ? WHERE id = ?",
        (obj.name, obj.email, obj.profile, obj.id)
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
    cursor.execute("DELETE FROM profile WHERE user_id = ?", (id,))
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
            email=item[2],
            profile=item[3]
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

# profile #

def db_create_profile(ctx:dict, obj:Profile) -> Profile:
    """
    create a profile in the database, verifying the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the data to create the profile with.

    return :: profile object with new id
    """

    if obj.id is not None:
        raise ValueError('cannot use profile with id to create new profile')

    obj.validate()

    cursor:sqlite3.Cursor = ctx['db']['cursor']

    # profile
    result = cursor.execute(
        "INSERT INTO profile(user_id, name, bio) VALUES(?, ?, ?)", 
        (obj.user_id, obj.name, obj.bio)
    )
    assert result.rowcount == 1
    assert result.lastrowid is not None
    obj.id = str(result.lastrowid)

    # profile.meta.data
    meta_data_rows = []
    for key, value in obj.meta.data.items():
        if isinstance(value, bool):
            meta_data_rows.append((obj.id, key, value, None, None, None))
        elif isinstance(value, int):
            meta_data_rows.append((obj.id, key, None, value, None, None))
        elif isinstance(value, float):
            meta_data_rows.append((obj.id, key, None, None, value, None))
        elif isinstance(value, str):
            meta_data_rows.append((obj.id, key, None, None, None, value))
        else:
            raise ValueError(f'unknown type for meta data value: {type(value)}')
    cursor.executemany(
        "INSERT INTO profile_meta_data(profile_id, key, value_bool, value_int, value_float, value_str) VALUES(?, ?, ?, ?, ?, ?)",
        meta_data_rows
    )

    # profile.meta.tags
    cursor.executemany(
        "INSERT INTO profile_meta_tags(profile_id, value, position) VALUES(?, ?, ?)", 
        [(obj.id, value, position) for position, value in enumerate(obj.meta.tags)]
    )

    # profile.meta.hierarchies
    cursor.executemany(
        "INSERT INTO profile_meta_hierarchies(profile_id, value, position) VALUES(?, ?, ?)", 
        [(obj.id, value, position) for position, value in enumerate(obj.meta.hierarchies)]
    )

    ctx['db']['commit']()
    return obj



def db_read_profile(ctx:dict, id:str) -> Profile:
    """
    read a profile from the database and verify it.

    args ::
        ctx :: dict containing the database client
        id :: the id of the profile to read.
    
    return :: profile object if it exists
    raises :: NotFoundError if the profile does not exist
    """
    
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    db_entry = cursor.execute("SELECT * FROM profile WHERE id = ?", (id,)).fetchone()
    if db_entry is None:
        raise NotFoundError(f'profile {id} not found')
    
    # profile.meta.data
    meta_data = {}
    for item in cursor.execute("SELECT * FROM profile_meta_data WHERE profile_id = ?", (id,)):
        key = item[2]
        
        # iterate over all values to find first non-null value
        for n, value in enumerate(item[3:]):
            if value is not None:
                # only bools need to be converted from sqlite3
                meta_data[key] = bool(value) if n == 0 else value
                break

    # profile.meta.tags
    meta_tags = []
    for item in cursor.execute("SELECT value FROM profile_meta_tags WHERE profile_id = ? ORDER BY position", (id,)):
        meta_tags.append(item[0])

    # profile.meta.hierarchies
    meta_hierarchies = []
    for item in cursor.execute("SELECT value FROM profile_meta_hierarchies WHERE profile_id = ? ORDER BY position", (id,)):
        meta_hierarchies.append(item[0])

    return Profile(
        id=str(db_entry[0]),
        user_id=str(db_entry[1]),
        name=db_entry[2],
        bio=db_entry[3],
        meta=Meta(
            data=meta_data,
            tags=meta_tags,
            hierarchies=meta_hierarchies
        )
    ).validate()


def db_update_profile(ctx:dict, obj:Profile) -> Profile:
    """
    update a profile in the database, and verify the data first.

    args ::
        ctx :: dict containing the database client
        obj :: the data to update the profile with.

    return :: profile object
    raises :: NotFoundError if the profile does not exist
    """
    obj.validate()

    if obj.id is None:
        raise ValueError('cannot update profile without id')
    
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    result = cursor.execute(
        "UPDATE profile SET user_id = ?, name = ?, bio = ? WHERE id = ?",
        (obj.user_id, obj.name, obj.bio, obj.id)
    )
    if result.rowcount == 0:
        raise NotFoundError(f'profile {obj.id} not found')
    
    # profile.meta.data
    cursor.execute("DELETE FROM profile_meta_data WHERE profile_id = ?", (obj.id,))
    meta_data_rows = []
    for key, value in obj.meta.data.items():
        if isinstance(value, bool):
            meta_data_rows.append((obj.id, key, value, None, None, None))
        elif isinstance(value, int):
            meta_data_rows.append((obj.id, key, None, value, None, None))
        elif isinstance(value, float):
            meta_data_rows.append((obj.id, key, None, None, value, None))
        elif isinstance(value, str):
            meta_data_rows.append((obj.id, key, None, None, None, value))
        else:
            raise ValueError(f'unknown type for meta data value: {type(value)}')
        
    cursor.executemany(
        "INSERT INTO profile_meta_data(profile_id, key, value_bool, value_int, value_float, value_str) VALUES(?, ?, ?, ?, ?, ?)",
        [(obj.id, key, value) for key, value in obj.meta.data.items()]
    )

    # profile.meta.tags
    cursor.execute("DELETE FROM profile_meta_tags WHERE profile_id = ?", (obj.id,))
    cursor.executemany(
        "INSERT INTO profile_meta_tags(profile_id, value, position) VALUES(?, ?, ?)", 
        [(obj.id, value, position) for position, value in enumerate(obj.meta.tags)]
    )
    
    # profile.meta.hierarchies
    cursor.execute("DELETE FROM profile_meta_hierarchies WHERE profile_id = ?", (obj.id,))
    cursor.executemany(
        "INSERT INTO profile_meta_hierarchies(profile_id, value, position) VALUES(?, ?, ?)", 
        [(obj.id, value, position) for position, value in enumerate(obj.meta.hierarchies)]
    )

    ctx['db']['commit']()
    return obj

    
def db_delete_profile(ctx:dict, id:str) -> None:
    """
    delete a profile from the database.

    args ::
        ctx :: dict containing the database client
        id :: the id of the profile to delete.

    return :: None
    """
    
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    cursor.execute("DELETE FROM profile WHERE id = ?", (id,))
    cursor.execute("DELETE FROM profile_meta_data WHERE profile_id = ?", (id,))
    cursor.execute("DELETE FROM profile_meta_tags WHERE profile_id = ?", (id,))
    cursor.execute("DELETE FROM profile_meta_hierarchies WHERE profile_id = ?", (id,))
    ctx['db']['commit']()


def db_list_profile(ctx:dict, offset:int=0, limit:int=25) -> list[Profile]:
    """
    list profiles from the database and verify them.

    args ::
        ctx :: dict containing the database client
        offset :: the offset to start listing from.
        limit :: the maximum number of items to list.

    return :: list of profile objects.
    """
    
    cursor:sqlite3.Cursor = ctx['db']['cursor']
    items = []

    for row in cursor.execute("SELECT * FROM profile ORDER BY id LIMIT ? OFFSET ?", (limit, offset)):
        # profile.meta.data
        meta_data = {}
        for item in cursor.execute("SELECT * FROM profile_meta_data WHERE profile_id = ?", (row[0],)):
            key = item[1]
            
            # iterate over all values to find first non-null value
            for n, value in enumerate(item[2:]):
                if value is not None:
                    # only bools need to be converted from sqlite3
                    meta_data[key] = bool(value) if n == 0 else value
                    break

        # profile.meta.tags
        meta_tags = []
        for item in cursor.execute("SELECT value FROM profile_meta_tags WHERE profile_id = ? ORDER BY position", (row[0],)):
            meta_tags.append(item[0])

        # profile.meta.hierarchies
        meta_hierarchies = []
        for item in cursor.execute("SELECT value FROM profile_meta_hierarchies WHERE profile_id = ? ORDER BY position", (row[0],)):
            meta_hierarchies.append(item[0])

        items.append(Profile(
            id=str(row[0]),
            user_id=str(row[1]),
            name=row[2],
            bio=row[3],
            meta=Meta(
                data=meta_data,
                tags=meta_tags,
                hierarchies=meta_hierarchies
            )
        ).validate())